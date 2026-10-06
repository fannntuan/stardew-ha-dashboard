/* Stardew Valley 主题辅助 v7：木质控件 + 游戏像素图标
   做法：
   1) document 级 CSS：卡片木箱框 / 木纹顶栏 / 羊皮纸背景 / 木滚动条
   2) 往相关卡片的 shadow root 注入样式（HA 卡片内部在 shadow DOM 里，页面级 CSS 够不着）
      - hui-markdown-card / ha-markdown → 导航木质按钮
      - hui-heading-card            → 木牌标题
      - hui-tile-card               → 格子内凹 + 图标替换规则
      - hui-button-card             → 木按钮
      - hui-view-header             → 羊皮纸横幅（"欢迎回家"）
   3) JS：按格子的中文名给 ha-tile-icon 打 data-sdv 标记，CSS 用精灵图替换 mdi 图标
   （HA 的图标是用属性 property 设的、DOM 上没有 icon= 属性，所以只能这样按名字映射）
   改完记得把 lovelace 资源 ?v=N 加一。 */
(function () {
  const ID = "stardew-theme-helper";
  const old = document.getElementById(ID);
  if (old) old.remove();

  const IMG = "/local/stardew/img";
  const G = IMG + "/game";
  const FONTS = "/local/stardew/fonts";

  /* ============ A. document 级 ============ */
  const css = `
  @font-face{font-family:"Stardew Pixel";font-style:normal;font-weight:400;font-display:swap;
    src:url("${FONTS}/stardew-pixel-latin.woff2") format("woff2");}
  @font-face{font-family:"Stardew Pixel";font-style:normal;font-weight:400;font-display:swap;
    src:url("${FONTS}/stardew-pixel-zh.woff2") format("woff2");
    unicode-range:U+2E80-33FF,U+3400-4DBF,U+4E00-9FFF,U+F900-FAFF,U+FE30-FE4F,U+FF00-FFEF,U+3000-303F;}

  html, body { -webkit-font-smoothing: none !important; text-rendering: optimizeSpeed !important; }
  img { image-rendering: pixelated; }

  /* 卡片 = 木箱：四角铆钉 + 羊皮纸噪点 + 硬阴影 */
  ha-card {
    border-style: solid !important;
    border-width: 5px !important;
    border-image: url("${G}/frame_crate.png?v=9") 5 / 5px / 0 stretch !important;
    border-radius: 0 !important;
    image-rendering: pixelated;
    background-image: url("${IMG}/paper_noise.png") !important;
    background-repeat: repeat !important;
    box-shadow: 0 3px 0 rgba(60,30,16,.4) !important;
  }
  /* 顶部「欢迎回家」→ 羊皮纸横幅（两端木轴 + 卷边）*/
  ha-card[data-sdv="banner"] {
    border-width: 4px !important;
    border-image: url("${G}/frame_banner.png?v=10") 4 / 4px / 0 stretch !important;
    background-color: #f9ecd0 !important;
    background-image: url("${IMG}/paper_noise.png") !important;
  }
  ha-card[data-sdv="banner"] ha-markdown h1,
  ha-card[data-sdv="banner"] h1 {
    color: #5a2b2a !important;
    text-shadow: 2px 2px 0 rgba(255,250,235,.85), 4px 4px 0 rgba(90,43,42,.18) !important;
  }

  /* 顶栏 / 侧边栏：木纹条 */
  ha-sidebar, .mdc-top-app-bar, ha-top-app-bar-fixed {
    background-image: url("${IMG}/wood_strip.png") !important;
    background-repeat: repeat !important; background-size: 32px 10px !important;
    image-rendering: pixelated !important;
  }
  ha-sidebar .menu .title {
    background-image: url("${IMG}/stardrop.png") !important;
    background-repeat: no-repeat !important; background-position: 8px center !important;
    background-size: 28px 28px !important; padding-left: 44px !important;
  }

  /* 页面背景：羊皮纸细纹 */
  ha-drawer > .mdc-drawer-app-content, home-assistant-main, hui-view {
    background-image: repeating-linear-gradient(0deg,
        rgba(120,80,40,.035) 0px, rgba(120,80,40,.035) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 4px),
      repeating-linear-gradient(90deg,
        rgba(120,80,40,.035) 0px, rgba(120,80,40,.035) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 4px);
  }

  ::-webkit-scrollbar { width: 12px; height: 12px; }
  ::-webkit-scrollbar-track { background: #e8d3a9; }
  ::-webkit-scrollbar-thumb { background: #8b5a2b; border: 2px solid #5a2b2a; border-radius: 0; }
  `;
  const s = document.createElement("style");
  s.id = ID;
  s.textContent = css;
  document.head.appendChild(s);

  /* ============ B. shadow DOM 注入的样式 ============ */
  const NAV_CSS = `
  a {
    display: inline-block !important; padding: 1px 10px 3px !important; margin: 2px 2px !important;
    color: #3f2410 !important; text-decoration: none !important; font-weight: 700 !important;
    line-height: 1.55 !important;
    border-style: solid !important; border-width: 3px !important;
    border-image: url("${IMG}/frame_button.png") 3 / 3px / 0 stretch !important;
    background-color: #e0a55f !important;
    box-shadow: 0 2px 0 rgba(60,30,16,.5), inset 0 1px 0 rgba(255,246,224,.55) !important;
    text-shadow: 0 1px 0 rgba(255,246,224,.6) !important;
  }
  a:active { transform: translateY(2px); box-shadow: inset 0 2px 3px rgba(60,30,16,.4) !important; }
  p:has(a[href*="/home-control/"]) > b {
    display: inline-block !important; padding: 1px 10px 3px !important; margin: 2px 2px !important;
    color: #ffeeb4 !important; line-height: 1.55 !important;
    border-style: solid !important; border-width: 3px !important;
    border-image: url("${IMG}/frame_sign.png") 3 / 3px / 0 stretch !important;
    background-color: #8a5a22 !important;
    box-shadow: inset 0 2px 4px rgba(40,20,8,.5) !important;
    text-shadow: 0 1px 0 rgba(0,0,0,.55) !important;
  }`;

  const HEAD_CSS = `
  h1, h2, h3, h4, h5, h6, .heading, .title {
    display: inline-block !important; padding: 1px 12px 3px !important;
    color: #ffeab4 !important;
    border-style: solid !important; border-width: 3px !important;
    border-image: url("${IMG}/frame_sign.png") 3 / 3px / 0 stretch !important;
    background-color: #a86c34 !important;
    text-shadow: 0 1px 0 rgba(0,0,0,.55) !important;
  }`;

  /* 顶部「欢迎回家」横幅：这张卡在 shadow DOM 里，只能注入到它所在的那个 root */
  const BANNER_CSS = `
  ha-card[data-sdv="banner"] {
    border-width: 4px !important; border-style: solid !important;
    border-image: url("${G}/frame_banner.png?v=10") 4 / 4px / 0 stretch !important;
    background-color: #f9ecd0 !important;
    background-image: url("${IMG}/paper_noise.png") !important;
    image-rendering: pixelated !important;
    box-shadow: 0 3px 0 rgba(60,30,16,.4) !important;
  }`;

  const BTN_CSS = `
  ha-card {
    background-color: #b9762f !important;
    background-image: url("${IMG}/wood_strip.png") !important;
    background-size: 24px 8px !important; background-blend-mode: multiply !important;
    box-shadow: inset 0 2px 0 rgba(255,235,190,.4), inset 0 -3px 0 rgba(60,28,8,.35),
                0 3px 0 rgba(60,30,16,.5) !important;
  }
  ha-card:active { transform: translateY(2px); }
  * { color: #fff3d2 !important; text-shadow: 0 2px 0 rgba(60,28,8,.8) !important; }`;

  /* 格子：内凹木感 + 用精灵图替换图标（JS 会打 data-sdv） */
  const SPRITES = ["torch_on", "torch_off", "lamp_on", "lamp_off", "ceiling", "string", "drop",
    "thermo", "oil", "washer", "fridge", "kettle", "filter", "printer", "vacuum", "battery",
    "door", "camera", "shield", "eye", "speaker", "tv", "curtain", "chest"];
  let iconRules = `
  ha-tile-container {
    box-shadow: inset 0 0 0 2px rgba(90,43,42,.18), inset 0 -3px 0 rgba(90,43,42,.14) !important;
  }
  ha-tile-icon[data-sdv] > * { visibility: hidden !important; }
  ha-tile-icon[data-sdv] {
    background-repeat: no-repeat !important; background-position: center !important;
    background-size: 26px 26px !important; image-rendering: pixelated !important;
  }`;
  for (const sp of SPRITES) {
    iconRules += `ha-tile-icon[data-sdv="${sp}"] { background-image: url("${G}/ic_${sp}.png") !important; }`;
  }
  /* 灯：开着用点亮的火把，关着用熄的 */
  iconRules += `
  ha-tile-icon[data-sdv="torch"][data-state="on"] { background-image: url("${G}/ic_torch_on.png") !important; }
  ha-tile-icon[data-sdv="torch"][data-state="off"] { background-image: url("${G}/ic_torch_off.png") !important; }
  ha-tile-icon[data-sdv="lamp"][data-state="on"] { background-image: url("${G}/ic_lamp_on.png") !important; }
  ha-tile-icon[data-sdv="lamp"][data-state="off"] { background-image: url("${G}/ic_lamp_off.png") !important; }
  /* 开着的灯：右下角再挂一个"木拉杆"小徽章，像游戏里拉下开关 */
  ha-tile-icon[data-state="on"] {
    background-repeat: no-repeat, no-repeat !important;
    background-position: center, right 2px bottom 2px !important;
    background-size: 26px 26px, 15px 15px !important;
  }
  ha-tile-icon[data-state="on"][data-sdv="torch"] {
    background-image: url("${G}/ic_torch_on.png"), url("${G}/lever_on.png") !important;
  }
  ha-tile-icon[data-state="on"][data-sdv="lamp"] {
    background-image: url("${G}/ic_lamp_on.png"), url("${G}/lever_on.png") !important;
  }`;
  const TILE_CSS = iconRules;

  const MAP = {
    "hui-markdown-card": ["nav", NAV_CSS],
    "ha-markdown": ["nav", NAV_CSS],
    "hui-heading-card": ["head", HEAD_CSS],
    "hui-tile-card": ["tile", TILE_CSS],
    "ha-tile-container": ["tile", TILE_CSS],
    "hui-button-card": ["btn", BTN_CSS],
  };

  /* 中文名 → 精灵图 key（按顺序匹配） */
  const NAME_RULES = [
    [/湿度|湿润/, "drop"],
    [/汽油|柴油|油价/, "oil"],
    [/洗衣机|洗涤|洗衣/, "washer"],
    [/冰箱|冷藏|冷冻|变温/, "fridge"],
    [/热水器|水温|加热/, "kettle"],
    [/净水|TDS|RO|滤芯|初滤|余氯/, "filter"],
    [/打印/, "printer"],
    [/扫地|清扫|回充/, "vacuum"],
    [/电量|电池/, "battery"],
    [/防盗门|门锁|门状态|门灯|玄关门口/, "door"],
    [/摄像|监控|天网/, "camera"],
    [/有人|人感|感应|无人/, "eye"],
    [/音箱|音响|播放|音乐/, "speaker"],
    [/电视|红外/, "tv"],
    [/帘/, "curtain"],
    [/布防|安防|报警/, "shield"],
    [/台灯|电脑灯/, "lamp"],
    [/灯|筒灯|灯带|壁灯|主灯|夜灯|照明/, "torch"],
    [/温度|客厅$|主卧$|书房$/, "thermo"],
    [/打印件|料盘|耗材/, "chest"],
  ];

  function inject(root, key, text) {
    if (!root || root.querySelector('style[data-sdv="' + key + '"]')) return;
    const st = document.createElement("style");
    st.setAttribute("data-sdv", key);
    st.textContent = text;
    root.append(st);
  }

  function markTiles(root) {
    let n = 0;
    for (const icon of root.querySelectorAll("ha-tile-icon")) {
      if (icon.getAttribute("data-sdv")) continue;
      const container = icon.closest("ha-tile-container");
      const nameEl = container && container.querySelector("span.primary");
      const name = nameEl ? nameEl.textContent.trim() : "";
      if (!name) continue;
      for (const [re, key] of NAME_RULES) {
        if (re.test(name)) { icon.setAttribute("data-sdv", key); n++; break; }
      }
    }
    return n;
  }

  function walk(node, root) {
    let els;
    try { els = node.querySelectorAll("*"); } catch (e) { return; }
    if (!root) root = document;
    for (const el of els) {
      const t = el.tagName ? el.tagName.toLowerCase() : "";
      /* 视图标题卡（text-only）→ 羊皮纸横幅 */
      if (t === "ha-card" && el.classList && el.classList.contains("text-only")) {
        el.setAttribute("data-sdv", "banner");
        inject(root, "banner", BANNER_CSS);
      }
      const sh = el.shadowRoot;
      if (sh) {
        const hit = MAP[t];
        if (hit) inject(sh, hit[0], hit[1]);
        markTiles(sh);
        walk(sh, sh);
      }
    }
  }

  let timer = null;
  function schedule() {
    if (timer) return;
    timer = setTimeout(function () { timer = null; try { walk(document); } catch (e) {} }, 300);
  }
  walk(document);
  try { new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true }); } catch (e) {}
  setTimeout(function () { try { walk(document); } catch (e) {} }, 1200);
  setTimeout(function () { try { walk(document); } catch (e) {} }, 3500);
})();
