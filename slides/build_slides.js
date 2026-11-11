// OTセキュリティ入門 前半スライド（AI生成画像入り・PowerPoint生成）
// 文字サイズ原則: タイトル44 / 本文28 / 詳細18 / 参考9（全スライドで統一）
// 矢印はブロック矢印シェイプで描く（line+矢じりは崩れるため不可）
// 実行: OUT=<出力先> IMG=<画像ディレクトリ> node build_slides.js
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 inch
p.author = "OT Security WS";

const IMG = process.env.IMG || "/Users/shunikeda/gitClones/ot-lab/ws1-ctf/slides/img";
const HERO = IMG + "/hero_overflow.png";
const ROOM = IMG + "/control_room.png";
const LOCK = IMG + "/security_breach.png";

// ---- 配色 ----
const NAVY="0E1A2B", NAVY2="16273B", INK="1A2432", CY="117E9B", CYBR="46D0EF",
      DANGER="D6334C", MUTED="6B7A8D", MUTED_D="C3D2E2",
      CARD="EEF3F7", CARDLINE="DCE6EE", WHITE="FFFFFF", PAPER="FFFFFF";
const HF="Calibri", BF="Calibri";
// ---- 文字サイズ（原則）----
const T=44, EB=18, B=28, D=18, REF=9;
const M=0.62, SW=13.33, SH=7.5;

function slide(bg){ const s=p.addSlide(); s.background={color:bg||PAPER}; return s; }
function cover(s,img,x,y,w,h){ s.addImage({path:img,x,y,w,h,sizing:{type:"cover",w,h}}); }
function scrim(s,x,y,w,h,color,tr){ s.addShape(p.ShapeType.rect,{x,y,w,h,
  fill:{color:color||NAVY,transparency:tr==null?45:tr},line:{type:"none"}}); }
function eyebrow(s,t,dark){ s.addText(t.toUpperCase(),{x:M,y:0.45,w:12,h:0.35,isTextBox:true,margin:0,
  fontFace:HF,fontSize:EB,bold:true,color:dark?CYBR:CY,charSpacing:3}); }
function title(s,runs,dark){ s.addText(runs,{x:M,y:0.92,w:12.1,h:1.2,isTextBox:true,margin:0,
  fontFace:HF,fontSize:T,bold:true,color:dark?WHITE:INK,lineSpacingMultiple:1.0}); }
function card(s,x,y,w,h,fill,tr,linecol){ s.addShape(p.ShapeType.roundRect,{x,y,w,h,
  rectRadius:0.08, fill:{color:fill||CARD,transparency:tr==null?0:tr},
  line:{color:linecol||CARDLINE,width:1}}); }
// ブロック矢印（塗り・線なし）。dir: "right"|"left"
function barrow(s,x,y,w,h,dir,color){ s.addShape(dir==="left"?p.ShapeType.leftArrow:p.ShapeType.rightArrow,
  {x,y,w,h,fill:{color:color||MUTED},line:{type:"none"}}); }
function dot(s,x,y,color){ s.addShape(p.ShapeType.ellipse,{x,y,w:0.2,h:0.2,fill:{color:color||CY},line:{type:"none"}}); }

// ===== 1: タイトル =====
(function(){ const s=slide(NAVY);
  cover(s,HERO,0,0,SW,SH); scrim(s,0,0,SW,SH,"081320",38); scrim(s,0,0,7.8,SH,"081320",28);
  s.addText("OTセキュリティ入門ハンズオン",{x:M,y:1.0,w:7.2,h:0.45,isTextBox:true,margin:0,
    fontFace:HF,fontSize:EB,bold:true,color:CYBR,charSpacing:3});
  s.addText([
    {text:"産業用通信 ",options:{color:WHITE}},{text:"Modbus",options:{color:CYBR}},
    {text:" で\n制御装置を乗っ取る",options:{color:WHITE}},
  ],{x:M,y:1.6,w:7.3,h:2.3,isTextBox:true,margin:0,fontFace:HF,fontSize:T,bold:true,
    lineSpacingMultiple:1.05,shadow:{type:"outer",color:"000000",opacity:0.5,blur:6,offset:2,angle:90}});
  s.addText("認証のない制御通信で、\nタンクを実際にあふれさせる体験。",
    {x:M,y:4.3,w:7.0,h:1.5,isTextBox:true,margin:0,fontFace:BF,fontSize:B,color:MUTED_D,lineSpacingMultiple:1.15});
  s.addText("前半 10分 基礎説明　／　後半 50分 演習（CTF形式）",
    {x:M,y:6.6,w:10,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:"9DB1C6"});
  s.addNotes("導入。Modbusで制御装置を乗っ取りタンクをあふれさせる体験。前半10分基礎、後半50分演習。");
})();

// ===== 2: ゴール =====
(function(){ const s=slide(NAVY);
  eyebrow(s,"今日のゴール",true);
  s.addText([
    {text:"攻撃を体験し、\n",options:{color:WHITE}},
    {text:"なぜ防げないか",options:{color:CYBR}},
    {text:"を理解する",options:{color:WHITE}},
  ],{x:M,y:1.25,w:12,h:1.9,isTextBox:true,margin:0,fontFace:HF,fontSize:T,bold:true,lineSpacingMultiple:1.03});
  card(s,M,3.5,12.1,1.15,"102033",0,"243B52");
  s.addText([
    {text:"やること：",options:{bold:true,color:WHITE}},
    {text:"タンクを",options:{color:WHITE}},
    {text:"あふれさせる",options:{bold:true,color:"FF8DA1"}},
  ],{x:M+0.35,y:3.5,w:11.4,h:1.15,isTextBox:true,margin:0,valign:"middle",fontFace:BF,fontSize:B});
  const items=["攻撃対象：制御装置（PLC）のシミュレータ","設計図は渡さない — 自分で解く","最後に「どう防ぐか」を考える"];
  items.forEach((t,i)=>{ const y=5.05+i*0.72; dot(s,M,y+0.07,CYBR);
    s.addText(t,{x:M+0.42,y:y-0.08,w:11.4,h:0.55,isTextBox:true,margin:0,fontFace:BF,fontSize:B,color:WHITE}); });
  s.addNotes("結論先行。目的は『なぜ防げないか』の理解。対象はPLCシミュレータ。設計図は渡さず自分で解く。最後に防御を議論。");
})();

// ===== 3: 制御の仕組み =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"まず、制御の仕組み");
  title(s,"制御装置がタンクの水位を自動で保つ");
  cover(s,ROOM,7.15,2.35,5.55,4.45);
  s.addText([
    {text:"PLCが水位を読み、ポンプをオン・オフして\n水位を一定に保つ。",options:{color:INK,breakLine:true}},
  ],{x:M,y:2.5,w:6.1,h:1.6,isTextBox:true,margin:0,fontFace:BF,fontSize:B,lineSpacingMultiple:1.2});
  const b=["停止水位でポンプを止める","安全インターロックで強制停止"];
  b.forEach((t,i)=>{ const y=4.3+i*0.95; dot(s,M,y+0.08,CY);
    s.addText(t,{x:M+0.42,y:y-0.1,w:6.0,h:0.8,isTextBox:true,margin:0,fontFace:BF,fontSize:B,color:INK,lineSpacingMultiple:1.1}); });
  s.addText("後半は、この制御装置を攻撃します。",
    {x:M,y:6.3,w:6.1,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:D,italic:true,color:MUTED});
  s.addNotes("PLCが水位を読みポンプを制御。停止水位と安全インターロックの二重の守り。これが攻撃対象。");
})();

// ===== 4: Modbusとは =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"通信のことば");
  title(s,"Modbus — 産業の標準プロトコル");
  // 左: やり取り
  card(s,0.7,2.9,3.1,1.3);
  s.addText("攻撃者",{x:0.7,y:2.9,w:3.1,h:1.3,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:B,bold:true,color:INK});
  card(s,5.4,2.9,3.1,1.3);
  s.addText("制御装置",{x:5.4,y:2.9,w:3.1,h:1.3,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:B,bold:true,color:INK});
  barrow(s,3.95,3.35,1.3,0.42,"right",CY);
  s.addText("読め / 書け",{x:3.5,y:2.5,w:2.2,h:0.35,isTextBox:true,align:"center",margin:0,fontFace:BF,fontSize:D,color:MUTED});
  s.addText("制御装置は要求に答えて値を返す（すべて平文）。",
    {x:0.7,y:4.5,w:7.8,h:0.9,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:INK,lineSpacingMultiple:1.2});
  // 右: データモデル
  card(s,8.9,2.5,3.8,3.9);
  s.addText("データの持ち方",{x:9.2,y:2.75,w:3.3,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:B,bold:true,color:CY});
  s.addText([
    {text:"コイル",options:{bold:true,color:INK}},{text:"：オン/オフ（例: ポンプ）",options:{color:INK,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:6}},
    {text:"レジスタ",options:{bold:true,color:INK}},{text:"：16bitの数値（例: 水位）",options:{color:INK,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:6}},
    {text:"ポート",options:{bold:true,color:INK}},{text:"：502（今回 5020）",options:{color:INK}},
  ],{x:9.2,y:3.35,w:3.3,h:2.8,isTextBox:true,margin:0,fontFace:BF,fontSize:D,lineSpacingMultiple:1.25});
  s.addNotes("依頼側が『何番を読め/書け』と送り機器が答えるだけ。データはコイル(オンオフ)とレジスタ(数値)。ポート502、今回5020。");
})();

// ===== 5: 3つの欠陥 =====
(function(){ const s=slide(NAVY);
  cover(s,LOCK,0,0,SW,SH); scrim(s,0,0,SW,SH,"070E18",52);
  s.addText("ここが弱点".toUpperCase(),{x:M,y:0.45,w:12,h:0.35,isTextBox:true,margin:0,fontFace:HF,fontSize:EB,bold:true,color:CYBR,charSpacing:3});
  s.addText("Modbus には 3つの構造的な欠陥がある",{x:M,y:0.92,w:12.1,h:1.1,isTextBox:true,margin:0,fontFace:HF,fontSize:T,bold:true,color:WHITE});
  const flaws=[["認証なし","誰でも書き込める"],["暗号化なし","通信は平文で丸見え"],["改ざん検知なし","偽の命令も実行する"]];
  const cw=3.85, gap=0.3, y=2.7, ch=2.2;
  flaws.forEach((f,i)=>{ const x=M+i*(cw+gap);
    card(s,x,y,cw,ch,"0C1826",12,"3A2130");
    s.addText(f[0],{x:x+0.3,y:y+0.35,w:cw-0.6,h:0.8,isTextBox:true,margin:0,fontFace:HF,fontSize:B,bold:true,color:"FF7A8E"});
    s.addText(f[1],{x:x+0.3,y:y+1.25,w:cw-0.6,h:0.8,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:"D7E2EE",lineSpacingMultiple:1.2}); });
  s.addText("入れた時点で、制御を好きに書き換えられる。",
    {x:M,y:5.5,w:12.1,h:0.9,isTextBox:true,margin:0,fontFace:BF,fontSize:B,bold:true,color:CYBR,align:"center",valign:"middle"});
  s.addNotes("3欠陥：認証なし・暗号化なし・改ざん検知なし。到達できた時点で制御を書き換えられる。");
})();

// ===== 6: 読める・書ける・落とせる =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"欠陥が何を招くか");
  title(s,"読める・書ける・落とせる");
  const rows=[["読める",CY,"盗聴・偵察（機密）"],["書ける",DANGER,"改ざん → 物理被害（完全性）"],["落とせる",MUTED,"妨害（可用性）"]];
  rows.forEach((r,i)=>{ const y=2.65+i*1.2;
    s.addShape(p.ShapeType.roundRect,{x:M,y:y,w:2.7,h:0.8,rectRadius:0.4,fill:{color:r[1]},line:{type:"none"}});
    s.addText(r[0],{x:M,y:y,w:2.7,h:0.8,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:B,bold:true,color:WHITE});
    barrow(s,3.6,y+0.25,0.7,0.3,"right",MUTED);
    s.addText(r[2],{x:4.6,y:y,w:8.0,h:0.8,isTextBox:true,margin:0,valign:"middle",fontFace:BF,fontSize:B,color:INK}); });
  s.addText("情報セキュリティの3要素（機密・完全性・可用性）がそのまま崩れる。",
    {x:M,y:6.4,w:12,h:0.45,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:MUTED});
  s.addNotes("読める＝盗聴(機密)、書ける＝改ざんで物理被害(完全性)、落とせる＝妨害(可用性)。CIAがそのまま崩れる。");
})();

// ===== 7: 演習の流れ =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"演習の流れ（CTF形式）");
  title(s,"偵察から始め、最後はあふれさせる");
  const steps=[["1","偵察"],["2","盗聴"],["3","ポンプ奪取"],["4","設定改ざん"],["5","安全無効化 → 溢水"]];
  steps.forEach((t,i)=>{ const y=2.2+i*0.86; const last=i===4;
    card(s,M,y,6.9,0.72,last?DANGER:CARD,0,last?DANGER:CARDLINE);
    s.addText(t[0],{x:M+0.15,y:y,w:0.6,h:0.72,isTextBox:true,align:"center",valign:"middle",fontFace:HF,fontSize:B,bold:true,color:last?WHITE:CY});
    s.addText(t[1],{x:M+0.85,y:y,w:5.9,h:0.72,isTextBox:true,valign:"middle",margin:0,fontFace:BF,fontSize:B,bold:true,color:last?WHITE:INK});
    if(last) s.addText("目的達成",{x:M+5.4,y:y,w:1.4,h:0.72,isTextBox:true,align:"right",valign:"middle",margin:0,fontFace:BF,fontSize:D,bold:true,color:WHITE}); });
  s.addText([
    {text:"攻撃に成功すると",options:{color:INK}},{text:"フラグ",options:{bold:true,color:CY}},
    {text:"がレジスタに出る。設計図は渡さず、観測して自分で当てる。",options:{color:INK,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:10}},
    {text:"ボーナス: ",options:{bold:true,color:DANGER}},
    {text:"制御装置の復旧（防御）／保守バックドア",options:{color:INK}},
  ],{x:8.0,y:2.5,w:4.7,h:3.6,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:INK,lineSpacingMultiple:1.3});
  s.addNotes("偵察→盗聴→ポンプ奪取→設定改ざん→安全無効化。段位5で二重の安全が外れてタンクが溢れる＝目的達成。溢水の証拠フラグと保守バックドアはボーナス。");
})();

// ===== 8: ルール =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"始める前に");
  title(s,"ルールと安全");
  card(s,M,2.7,12.1,1.7,"FBECEE",0,"F2C9CF");
  s.addText("本編は AI 禁止",{x:M+0.4,y:2.95,w:11,h:0.6,isTextBox:true,margin:0,fontFace:HF,fontSize:B,bold:true,color:DANGER});
  s.addText("レジスタの意味を推定する部分は自分で読み解く。Wireshark や Modbus 全般の調べ物に AI を使うのは可。",
    {x:M+0.4,y:3.6,w:11.3,h:0.7,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:INK,lineSpacingMultiple:1.2});
  const bl=["詰まったら司会にヒントを求める","隔離されたネットワーク専用で行う"];
  bl.forEach((t,i)=>{ const y=4.95+i*0.8; dot(s,M,y+0.08,CY);
    s.addText(t,{x:M+0.42,y:y-0.1,w:11.4,h:0.6,isTextBox:true,margin:0,fontFace:BF,fontSize:B,color:INK}); });
  s.addNotes("本編はAI禁止（自分で読み解く。Wireshark等の調べ物は可）。詰まったら司会にヒント。隔離ネット専用。");
})();

// ===== 9: 今日使うツール =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"今日使うツール");
  title(s,"準備するのは、この3つ");
  const tools=[
    ["Python 3","攻撃ツール mbclient.py を動かす（追加ライブラリ不要）","入れ方: Windows は python.org（Add to PATH）/ Mac は標準 or brew"],
    ["Wireshark","暗号化されていない通信を覗いて中身を見る","入れ方: wireshark.org（Mac: ChmodBPF / Win: Npcap も入れる）"],
    ["Webブラウザ","問題とフラグ提出（CTFd）を開く","入れ方: 普段使っているものでOK"],
  ];
  tools.forEach((t,i)=>{ const y=2.2+i*1.32;
    card(s,M,y,12.1,1.15);
    s.addText(t[0],{x:M+0.35,y:y,w:3.3,h:1.15,isTextBox:true,valign:"middle",margin:0,fontFace:HF,fontSize:B,bold:true,color:CY});
    s.addText([{text:t[1],options:{color:INK,breakLine:true}},{text:t[2],options:{color:MUTED}}],
      {x:M+3.8,y:y,w:8.1,h:1.15,isTextBox:true,valign:"middle",margin:0,fontFace:BF,fontSize:D,lineSpacingMultiple:1.25}); });
  s.addText("（任意）nmap … ポート探索をやりたい人向け。無くても進められます。",
    {x:M,y:6.3,w:12,h:0.45,isTextBox:true,margin:0,fontFace:BF,fontSize:D,color:MUTED});
  s.addNotes("今日使うのはPython3(mbclient用・追加ライブラリ不要)、Wireshark(通信を覗く)、ブラウザ(CTFd)。任意でnmap。Wiresharkのキャプチャ権限は事前に一度試しておくと安心。");
})();

// ===== 10: 開始 =====
(function(){ const s=slide(NAVY);
  cover(s,HERO,0,0,SW,SH); scrim(s,0,0,SW,SH,"081320",55);
  s.addText("さあ、始めましょう".toUpperCase(),{x:M,y:0.6,w:12,h:0.35,isTextBox:true,margin:0,fontFace:HF,fontSize:EB,bold:true,color:CYBR,charSpacing:3});
  s.addText("接続して、制御装置を読んでみる",{x:M,y:1.05,w:12.1,h:1.1,isTextBox:true,margin:0,fontFace:HF,fontSize:T,bold:true,color:WHITE});
  card(s,M,2.7,5.9,1.6,"0E2033",10,"243B52");
  s.addText("問題とフラグ提出（CTFd）",{x:M+0.35,y:2.9,w:5.2,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:B,bold:true,color:WHITE});
  s.addText("http://<司会のIP>:8000",{x:M+0.35,y:3.5,w:5.3,h:0.6,isTextBox:true,margin:0,fontFace:HF,fontSize:D,bold:true,color:CYBR});
  card(s,M+6.2,2.7,5.9,1.6,"0E2033",10,"243B52");
  s.addText("制御装置（攻撃対象）",{x:M+6.55,y:2.9,w:5.2,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:B,bold:true,color:WHITE});
  s.addText("<司会のIP>:5020",{x:M+6.55,y:3.5,w:5.3,h:0.6,isTextBox:true,margin:0,fontFace:HF,fontSize:D,bold:true,color:CYBR});
  s.addText("mbclient.py で、まず保持レジスタを読んでみよう。",
    {x:M,y:4.7,w:12,h:0.6,isTextBox:true,margin:0,fontFace:BF,fontSize:B,color:MUTED_D});
  s.addShape(p.ShapeType.roundRect,{x:M,y:5.5,w:12.1,h:0.9,rectRadius:0.06,fill:{color:"05101C",transparency:8},line:{color:"24384F",width:1}});
  s.addText("python3 mbclient.py --host <IP> read-hr 0 30",
    {x:M+0.3,y:5.5,w:11.5,h:0.9,isTextBox:true,margin:0,valign:"middle",fontFace:"Courier New",fontSize:D,color:"7BE3B0"});
  s.addNotes("CTFdは司会のIP:8000、制御装置は:5020。まずmbclientで保持レジスタを読む。ここから偵察へ。");
})();

// ===== 11: インストール手順（付録・困ったとき用） =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"付録：インストール手順");
  title(s,"困ったときはこのコマンドで");
  const MONO="Courier New";
  // 左: Python
  card(s,M,2.2,5.85,4.7);
  s.addText([
    {text:"Python 3",options:{bold:true,color:CY,breakLine:true}},
    {text:"mbclient.py を動かすため",options:{color:MUTED,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:8}},
    {text:"Mac:  ",options:{color:INK}},{text:"brew install python",options:{fontFace:MONO,color:INK,breakLine:true}},
    {text:"Win:  ",options:{color:INK}},{text:"winget install Python.Python.3.12",options:{fontFace:MONO,color:INK,breakLine:true}},
    {text:"      （python.org は「Add to PATH」に✓）",options:{color:MUTED,breakLine:true}},
    {text:"Linux: ",options:{color:INK}},{text:"sudo apt install python3",options:{fontFace:MONO,color:INK,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:8}},
    {text:"確認: ",options:{color:INK}},{text:"python3 --version",options:{fontFace:MONO,color:INK}},
  ],{x:M+0.35,y:2.45,w:5.2,h:4.3,isTextBox:true,margin:0,fontFace:BF,fontSize:D,lineSpacingMultiple:1.3});
  // 右: Wireshark + nmap
  card(s,M+6.25,2.2,5.85,4.7);
  s.addText([
    {text:"Wireshark",options:{bold:true,color:CY,breakLine:true}},
    {text:"通信を覗くため",options:{color:MUTED,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:8}},
    {text:"Mac:  ",options:{color:INK}},{text:"brew install --cask wireshark",options:{fontFace:MONO,color:INK,breakLine:true}},
    {text:"Win:  wireshark.org の installer",options:{color:INK,breakLine:true}},
    {text:"      （Npcap も一緒に入れる）",options:{color:MUTED,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:10}},
    {text:"nmap（任意）",options:{bold:true,color:CY,breakLine:true}},
    {text:"Mac:  ",options:{color:INK}},{text:"brew install nmap",options:{fontFace:MONO,color:INK,breakLine:true}},
    {text:"Win:  ",options:{color:INK}},{text:"winget install Insecure.Nmap",options:{fontFace:MONO,color:INK}},
  ],{x:M+6.6,y:2.45,w:5.2,h:4.3,isTextBox:true,margin:0,fontFace:BF,fontSize:D,lineSpacingMultiple:1.3});
  s.addNotes("インストールに困った人向けの付録。Python3はmbclient用。Wiresharkは通信観察（Mac:ChmodBPF/Win:Npcap）。nmapは任意。");
})();

const OUT = process.env.OUT || "ot-intro.pptx";
p.writeFile({ fileName: OUT }).then(f=>console.log("wrote",f));
