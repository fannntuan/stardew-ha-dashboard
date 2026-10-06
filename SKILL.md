---
name: stardew-ha-dashboard
description: 把 HA 面板做成星露谷游戏风 + 米家摄像头接真·实时流（shadow DOM 注入、像素素材、kiosk 全屏、go2rtc miss 源、无头截图自检）。
---

# 星露谷风 Home Assistant 面板 + 摄像头实时流

## 何时使用

- 要给 Home Assistant / Lovelace 换皮肤，做成**游戏风**（木牌/木箱/像素图标/像素字体/全屏 kiosk）
- 要在**无头环境**里改 HA 仪表盘、主题、Lovelace 资源，并**截图自检**（NAS/服务器上没有能用的浏览器 UI）
- **米家/小米摄像头**在 HA 里只有"最后一次事件截图"，想接**真·实时画面**
- 要无头运维 NAS 上的 HA **虚拟机**（快照/开关机）
- 适配版本：HA Core 2026.9.x（冬瓜 HAOS 14.2.1，跑在 fnOS NAS 的 KVM 虚拟机里）

## 0. 环境准备

| 项 | 说明 |
| --- | --- |
| HA 连接 | 环境变量 `HA_BASE`（**80 端口才是 HA 本体**，8123 会 307 跳转）、`HA_USER`、`HA_PWD`；`scripts/ha_api.py` 走 auth flow 拿 token 并缓存 |
| 依赖 | `websockets`、`cryptography`、`Pillow`、`requests`；截图另需一个开了 CDP 的 Chrome（本例 `127.0.0.1:16002`） |
| 数据通道 | 改配置走 HA **REST/WS**；改 `/config` 下的文件走 **Samba**（`scripts/ha_file.py`，smbclient） |
| 常见工具 | `ha_api.py`（登录/rest/ws）、`ha_file.py`（get/put/ls）、`ha_shot.py`（截图）、`ha_card.py`（单卡截图）、`ha_dom.py`（DOM 结构）、`ha_imgcheck.py`（图片尺寸核对）、`ha_navtest.py`（导航点击验证） |

```bash
export HA_BASE=http://${HA_HOST}; export HA_USER=<账号>; export HA_PWD=<密码>
python3 scripts/ha_api.py rest GET /api/config
python3 scripts/ha_api.py ws '{"id":1,"type":"lovelace/resources"}'
```

> ⚠️ **WS 客户端坑**：`websocket-client` 的 recv 会拿到二进制 ping/pong 帧，必须先判类型再 `json.loads`；WS 命令必须带 `id`，否则 `Message incorrectly formatted`。返回里前两帧是 `auth_required/auth_ok`，要按 `id` 取结果，别写死 `[0]`。

## 1. 主题：5 套季节皮肤 + 像素字体

- 主题文件放 `/config/themes/*.yaml`，`configuration.yaml` 需有 `frontend: themes: !include_dir_merge_named themes`。
- 文件内容**必须是 `主题名: {变量…}` 的命名映射**，顶层直接写变量表会报 `expected a mapping`。
- 改完文件**等 ~10s 再 `frontend.reload_themes`**（HA 缓存解析结果，连着重载会拿到旧结果）。
- 关键变量：`ha-card-background`、`ha-font-family-body`、`ha-card-border-radius`、`ha-card-border-width`、`ha-border-radius-pill`、`ha-card-box-shadow`、`sidebar-background-color`、`state-light-active-color`、`mdc-theme-primary`…（= CSS 变量去掉 `--`）。
- 像素风要点：`ha-card-border-radius: 2px` + `border-width: 3px` + 硬阴影 `3px 3px 0 0 rgba(...)`，字号锁成 12 的倍数。
- **生效方式**：`POST /api/services/frontend/set_theme {"name":"stardew_fall"}`（比 `frontend/set_user_data` 可靠；用户若在「个人资料→主题」手动选过，会盖过默认主题）。
- **像素字体零外网依赖**：TakWolf/fusion-pixel-font 的 12px proportional woff2（OFL），放 `/config/www/<dir>/fonts/`，`@font-face` 用 `/local/<dir>/...` 引用，再加 `html{-webkit-font-smoothing:none}`。
- 生成脚本：`scripts/make_stardew_theme.py`（`BASE` 打底 + `PALETTES[name]` 覆盖 → 春/夏/秋/冬/夜 5 套）。
- **按季节自动换肤**：别用 `season` 集成（HA 2026.9 的 YAML 设置会报 `does not support YAML setup`），直接用按月份判断的自动化：

```yaml
- id: stardew_season_theme
  alias: 星露谷 · 按季节自动换皮肤
  trigger:
    - platform: time
      at: "00:05:00"
    - platform: homeassistant
      event: start
  action:
    - service: frontend.set_theme
      data:
        name: >-
          stardew_{% set m = now().month %}{{ 'spring' if m in [3,4,5] else ('summer' if m in [6,7,8] else ('fall' if m in [9,10,11] else 'winter')) }}
  mode: single
```

## 2. 让面板"像游戏"：shadow DOM 注入（核心技巧）

**根因**：HA 卡片的内容几乎都在 **shadow DOM** 里，`document.head` 的 CSS 够不着（给 `ha-markdown-element a` 写样式完全不生效）。

做法（`scripts/stardew.js`）：

```js
const MAP = {"hui-markdown-card":NAV_CSS, "ha-markdown":NAV_CSS,
             "hui-heading-card":HEAD_CSS, "hui-tile-card":TILE_CSS, "hui-button-card":BTN_CSS};
function walk(node, root){                       // 递归遍历，一路带着"当前 root"
  if (node.shadowRoot) { inject(node.shadowRoot, ...); walk(node.shadowRoot, node.shadowRoot); }
  node.children?.forEach(c => walk(c, root));
}
new MutationObserver(debounce(() => walk(document, document), 300)).observe(document, {childList:true,subtree:true});
```

- `ha-card` **这种宿主元素是够得着的** → "卡片外框"用全局 CSS，"卡片内部文字/按钮"用 shadow 注入，分两层写。
- shadow 内只对某一段生效：用 `p:has(a[href*="/home-assistant/"]) > b`，别写裸 `b`（会误伤标题里的加粗数值）。
- ⚠️ **`!important` 胜负规则**：外层（document）的 `!important` **赢过** shadow 内层的 `!important`；普通声明反过来。所以要覆盖卡片边框，要么把规则注入到**目标元素所在的那个 shadow root**，要么给元素打属性用更高特异性选择器（`ha-card[data-sdv="banner"]`）。
- ⚠️ **HA 的 `markdown` 卡片会剥掉整个 `style` 属性**（`getAttribute('style')` 为空）→ 想在 markdown 里控制图片大小只能**把尺寸烤进图片文件**；换行只能用 `<br>`，`flex-wrap` 无效。
- ⚠️ **换掉的图片必须改 URL**（`?v=N`），否则浏览器一直用缓存旧图（现象：服务端已是 28×20，页面 `naturalWidth` 还是 126×90）。
- 改完 `stardew.js` 要把 Lovelace 资源的 URL 版本号 +1（`lovelace/resources/update`，不用重启）。

### 木质控件（border-image 9 宫格）

```css
.wood { border-width:3px; border-image:url(/local/stardew/img/frame_sign.png) 3 / 3px / 0 stretch;
        border-radius:0; image-rendering:pixelated;
        box-shadow:0 2px 0 rgba(60,30,16,.5), inset 0 1px 0 rgba(255,246,224,.55); }
.wood:active{ transform:translateY(2px); }
```

- 深木底上的文字要用**浅色**（`#fff3d2` + `text-shadow:0 2px 0 rgba(60,28,8,.8)`），深棕字在深木纹上看不清。
- 做"木箱卡片"用 16×16 / 5px 切片，**铆钉必须画在角切片内**；矮卡片（标题条）改 4px 切片。
- 用真素材取色更还原：拿游戏 UI 部件图沿边框扫一行像素得到层色（如 `#5a2b2a → #dc7b05 → #a84a08 → #e6a461`），再自己画 9 宫格。**不要用 `fill`**，否则盖掉卡片底色。

### 换像素图标（按格子名字匹配）

HA 的图标是 **JS property 设的**，DOM 上没有 `icon="mdi:..."` 属性 → 不能用图标名写 CSS。
可用钩子：`ha-tile-icon` 上的 `data-domain` / `data-state`；sensor 域区分不了温度/湿度/电量，所以：

```js
// 1) 按格子的中文名给 ha-tile-icon 打标记
icon.dataset.sdv = matchName(tileText);   // /湿度/→drop、/汽油|柴油/→oil、/洗衣机/→washer …
// 2) 注入到 tile 卡片的 shadow root
ha-tile-icon[data-sdv] > * { visibility:hidden !important; }
ha-tile-icon[data-sdv="torch"] { background:url(/local/stardew/img/game/ic_torch_on.png) center/26px 26px no-repeat; }
ha-tile-icon[data-sdv="torch"][data-state="off"] { background-image:url(.../ic_torch_off.png); }   /* 按状态换明暗 */
```

- 名字匹配表**顺序敏感**（先特后泛）。
- 自绘图标生成器：`scripts/gen_game_icons.py`（火把/台灯/顶灯/灯串/水滴/温度计/油桶/洗衣机/冰箱/水壶/滤芯/打印机/扫地机/电池/木门/摄像头/盾牌/眼睛/音箱/电视/窗帘/木箱 + 木箱框 + 羊皮纸横幅 + 木拉杆）。预置产物见 `assets/icons/`。

## 3. 全屏 kiosk + 自绘导航

HA 本身没有全屏开关；标准解法是 **kiosk-mode**（NemesisRE/kiosk-mode，HACS 前端插件）。

- **HACS 装不动时手动装**（HACS 从 github.com 拉 zip，半通环境会卡）：`GET https://api.github.com/repos/NemesisRE/kiosk-mode/releases/latest` → 用资产的 `url` + `Accept: application/octet-stream` 下载 → Samba 传到 `www/kiosk-mode.js` → WS `lovelace/resources/create {res_type:"module", url:"/local/kiosk-mode.js"}`（**不用重启**）。
- 配置写在**仪表盘自己的 raw config 顶层**（每个仪表盘一份，改完刷新页面即生效）：

```yaml
kiosk_mode:
  kiosk: true        # 同时隐藏 header + sidebar
views: ...
```

- 临时关掉（要编辑仪表盘时）：网址后加 **`?disable_km`**。
- ⚠️ **顶栏没了 = HA 自带的视图标签也没了** → 多视图仪表盘会被锁在首页。必须自己导航：给每个视图第一个 section 插一条 markdown 链接（实测同源相对链接会走前端路由，URL 跟着变）：

```html
<img src='/local/stardew/img/hud_stardrop.png'> <b>主页</b>　<a href='/home-control/living'>客厅</a> …
```

- **视图的 `header` 卡片不会被 kiosk 藏掉**（渲染在内容区）→ 用户自己加的「欢迎回家」横幅在 kiosk 下依然显示。
- 验证：`scripts/ha_navtest.py <路径> <链接文字>` —— 打开页面、真实点击、打印点击前后 `location.href`。

## 4. 小米 / 米家摄像头接"真·实时"

### 4.1 先认清限制

- 米家**云接入**的设备，miot 用的是转换器类 `CameraEntity`：`image_source()` = **最近一次事件的截图**，`stream_source()` = 那次事件的加密 m3u8 片段。
  这就是"画面有，但一直是几个小时前那张"的原因（画面里可能还印着当时的时间戳）。
- 有实时流能力的 `MiotCameraEntity` **只在局域网/token 接入时创建** → 在 `device_customizes` 里写 `use_rtsp_stream: true` 对云接入**完全无效**。
- 实测这台 ipc019 的三条云路线都断：Alexa `start_rtsp_stream` 被设备拒（`-2003`）；Google `start_hls_stream` 返回了转码地址但**持续 404**；摄像头局域网 **TCP 端口全关**（没有 RTSP/ONVIF）。
- 顺带两个坑：miot 的 `BaseCameraEntity` 设的是 `self._supported_features`（**少了 `_attr_`**），HA 2026.9 读的是 `_attr_supported_features` → miot 摄像头 `supported_features` 恒为 0，前端不给"实时流"入口；摄像头属性**别走本地**（`No response from the device <lan_ip>`），云端走 `device.cloud.async_get_properties_for_mapping`。

### 4.2 用 go2rtc 的 `xiaomi`（miss/P2P）源 —— 实测可行

go2rtc（AlexxIT）从 **v1.9.13** 起支持小米相机的 `miss` 协议：**本地 P2P 直连**（米家 App 就是这条路），**不需要摄像头开放任何端口**，只要小米账号 token（登录要邮箱/短信验证码，可在 go2rtc WebUI 里让用户自己登，token 会自动写进配置）。

```yaml
# go2rtc 配置（示例见 assets/go2rtc.example.yaml）
xiaomi:
  "${XIAOMI_UID}": "V1:***<YOUR_XIAOMI_TOKEN>***"
streams:
  micam1: [xiaomi://${XIAOMI_UID}:cn@${CAMERA_IP}?did=${CAMERA_DID}&model=chuangmi.camera.ipc019]  # 原始 H265
  micam1_h264: [ffmpeg:micam1#video=h264#width=1280#height=720]                                     # 浏览器/HA 只吃 H264
```

- **不用碰容器里的文件**（没 docker 权限也能改）：
  - `GET /api/config` 读、`POST /api/config`（body = 完整 YAML）整体替换并持久化
  - `PUT /api/streams?name=X&src=Y` 加流（⚠️ `src` **不能有空格**，否则 `source with spaces may be insecure`）
  - `GET /api/streams` 看状态（consumers/producers/协议）；`GET /api/frame.jpeg?src=X` 取帧
  - 播放：`rtsp://<nas>:8554/<name>`、`/api/stream.m3u8?src=X`
- ⚠️ **`#hardware` 在没有 `/dev/dri` 的容器里转不出流**（会 404/绿屏）→ 转码源别带；`ffmpeg:` 源**按需启动**，不看时不烧 CPU。
- ⚠️ **取静帧要用原始流**（`?src=micam1`）：转码流的 `frame.jpeg` 会返回**纯绿帧**（H265 起始 GOP 没同步，实测 5.6KB 绿图 vs 原始流 139KB 正常图）。
- **接进 HA**（HA 2026.9 起 `generic` camera **已不是 YAML platform**，写 `camera: - platform: generic` 会报
  `The generic platform for the camera integration does not support platform setup`）→ 走 **config flow**：

```python
POST /api/config/config_entries/flow {"handler":"generic"}
# → step user: {stream_source, still_image_url, username, password,
#               advanced:{framerate:15, verify_ssl:true, rtsp_transport:"tcp"}}
# → step user_confirm: {"confirmed_ok": true} → create_entry
```

  - ⚠️ 校验会**真连流**（约 10s 超时）→ 转码流要先预热，否则 `errors.stream_source='timeout'`：
    `ffmpeg -v error -rtsp_transport tcp -i rtsp://127.0.0.1:8554/micam1_h264 -c copy -f null - &` 等 10~15s 再提交。
  - `stream_source = rtsp://<nas>:8554/micam1_h264`，`still_image_url = http://<nas>:1984/api/frame.jpeg?src=micam1`。
  - 实体名默认是 `camera.192_168_x_x` → 用 `config/entity_registry/update`（`new_entity_id` + `name`）改成中文；改参数走 **options flow**（同字段）。需要 `advanced` 里的必填键，缺了报 `required key not provided at 'advanced.framerate'`。
  - 验收：连续 `GET /api/camera_proxy/<eid>` **三次 md5 都不同** = 真·实时 ✓（静态事件截图会三次一样）。
- 面板卡片：`{"type":"picture-entity","entity":"camera.xxx","camera_view":"live","show_state":false}`（generic camera 有 `stream_source` 会自动置 STREAM 特性，前端才给实时流入口）。
- **首次打开有 ~8-10s 启动延迟**（P2P 建连 + 软件转码），之后实时；电池类门铃**没有 miss 流服务**，做不了实时。

## 5. 仪表盘工程规矩（多视图 + 用户手改）

- **只改部分视图**：生成脚本 `--apply` 时**按 `path` 匹配、保持线上视图顺序**，只替换要改的视图，其余从线上原样带回：

```python
live = WS("lovelace/config")["result"]
gen  = {v["path"]: v for v in DASH["views"]}
out  = dict(live)
out["views"] = [(v if v["path"] == "main" else gen.get(v["path"], v)) for v in live["views"]]
out["views"] += [v for v in DASH["views"] if v["path"] not in {x["path"] for x in live["views"]}]
WS("lovelace/config/save", config=out)
```

  ⚠️ 别写 `[live["views"][0]] + DASH["views"][1:]` —— 用户一旦拖动过视图顺序，主页就会被覆盖（踩过）。改完**回读并做字节级比对**（`json.dumps(..., sort_keys=True)`）确认没动的视图真的没变，改前先存 `dashboard_before_*.json` 快照。
- 用户会在界面上自己改（加 header 横幅、拖动顺序、调整行铺满）→ 这些改动要**同步回生成脚本**，否则下次重建会抹掉。
- **排版配方**：每段加 `heading` 木牌标题（没标题的页面就是"一堆格子"）；宽卡与格子并排用 section `column_span: 2/3`（典型：`[thermostat, grid(开关)]`、`[picture-entity(摄像头), grid(状态)]`）；`grid` 的 `columns` 按最长名字定（中文名 4 列会被截成"客厅…"，3 列刚好、长名字 2 列）。
- ⚠️ **卡在 grid 里会被拉伸到同行最高那张**（内容少的卡出现大片空白）→ 要么给卡补真实内容，要么让同行卡片内容量接近。
- ⚠️ HA sections 视图按**视口 CSS 宽**算列数（~1040px → 2 列；**~1536px（横屏平板）→ 3 列**）；截图要 `ha_shot.py <path> <out> 1536 900 desktop`（第 5 个参数 `desktop` 关掉手机模拟）。
- **截图自检三件套**：`ha_shot.py`（长图，`captureBeyondViewport`）、`ha_card.py`（单卡局部放大，含**滚动预热**：HA 懒渲染，屏外卡不在 DOM 里）、`ha_dom.py`（dump 真实元素/类名写精确选择器）。
  判断换肤是否生效**只看顶栏+背景色**最快；截图报错页时脚本应打印"页面打不开"（踩过：路径没带 `/lovelace` 时把错误页当成功）。

## 6. 无头运维 NAS 上的 HA 虚拟机

- fnOS 的「虚拟机」应用 `trim.vm` 自带 HTTP API（`/vm/api/v1/...`，nginx 5666/5667），鉴权用 fnOS 门户 token（`Authorization: <token>` 裸 token）。
- **GET 的参数要放 query string**（`GET /snapshot/list?name=<vmName>`）；**POST 用 JSON body**。参数名：`{"name": <vmName>, "snapshotName": ..., "snapshotDesc": ""}`。
- ⚠️ **EFI 虚拟机不支持在线快照**：`online snapshots are not supported for running EFI virtual machines` → 必须先 `POST /domain/shutdown` 等 `SHUTOFF`，建完快照再 `POST /domain/start`（HA 冷启动约 1~2 分钟，实体从 0 涨到 400+ 才算起完）。工具：`scripts/vm_snap.py`（`status/shutdown/create/start/full`）。
- 排障：HA 报错日志走 WS `system_log/list`（**只收 WARNING 及以上**）；`/config/home-assistant.log` 常常是 0 字节的 `.fault`，supervisor `/core/logs` 也可能返回 null —— 别指望日志文件。
- 调试第三方集成(如 miot)时可在 `.py` 里插 `_LOGGER.warning(...)` 再重启，靠 `system_log/list` 抓；**记得还原原始文件**。

## 7. 快速命令速查

```bash
# 主题 / 资源
WS frontend/set_theme {name:"stardew_fall"}          |  POST /api/services/frontend/set_theme
WS lovelace/resources/create {url:"/local/stardew/stardew.js?v=7", res_type:"module"}
WS lovelace/config {url_path:"home-control"}         # 读仪表盘
WS lovelace/config/save {url_path:"home-control", config:{...}}

# 截图 / 结构
python3 scripts/ha_shot.py home-control/security /tmp/s.png 1536 900 desktop
python3 scripts/ha_card.py home-control 今日油价 /tmp/card.png
python3 scripts/ha_dom.py home-control/main

# 摄像头
curl http://<nas>:1984/api/streams | jq
curl -o /tmp/f.jpg "http://<nas>:1984/api/frame.jpeg?src=micam1"
ffprobe -v error -rtsp_transport tcp -show_entries stream=codec_name,width,height rtsp://<nas>:8554/micam1_h264

# 虚拟机快照（EFI 需关机）
python3 scripts/vm_snap.py full "2026-10-06 面板+摄像头"
```

## 8. 许可

- 本技能/仓库的代码、主题、**自绘像素图标**可自由使用（建议注明出处）。
- **不分发任何《星露谷物语》游戏素材**；主题里的调色/风格为自绘复刻，版权归原作者 ConcernedApe。
- 所有凭据、token、内网地址在示例里均为占位符（`${HA_PWD}`、`${NAS_IP}`、`${XIAOMI_UID}` …）——**别把真密码写进脚本**。
