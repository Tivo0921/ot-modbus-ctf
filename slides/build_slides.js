// OTセキュリティ入門 前半スライド（AI生成画像入り・PowerPoint生成）
// 実行: OUT=<出力先> IMG=<画像ディレクトリ> node build_slides.js
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 inch
p.author = "OT Security WS";

const IMG = process.env.IMG || "/Users/shunikeda/gitClones/ot-lab/ws1-ctf/slides/img";
const HERO = IMG + "/hero_overflow.png";       // 溢水タンク
const ROOM = IMG + "/control_room.png";        // 制御盤/PLC/ネットワーク
const LOCK = IMG + "/security_breach.png";     // 破られた施錠

// ---- 配色 ----
const NAVY="0E1A2B", NAVY2="16273B", INK="1A2432", CY="117E9B", CYBR="46D0EF",
      DANGER="D6334C", GREEN="1F9E6B", MUTED="6B7A8D", MUTED_D="C3D2E2",
      CARD="EEF3F7", CARDLINE="DCE6EE", WHITE="FFFFFF", PAPER="FFFFFF";
const HF="Calibri", BF="Calibri";
const M=0.62, SW=13.33, SH=7.5;

function slide(bg){ const s=p.addSlide(); s.background={color:bg||PAPER}; return s; }
function cover(s,img,x,y,w,h){ s.addImage({path:img,x,y,w,h,sizing:{type:"cover",w,h}}); }
function scrim(s,x,y,w,h,color,tr){ s.addShape(p.ShapeType.rect,{x,y,w,h,
  fill:{color:color||NAVY,transparency:tr==null?45:tr},line:{type:"none"}}); }
function eyebrow(s,t,dark){ s.addText(t.toUpperCase(),{x:M,y:0.42,w:12,h:0.3,isTextBox:true,margin:0,
  fontFace:HF,fontSize:12,bold:true,color:dark?CYBR:CY,charSpacing:3}); }
function title(s,runs,dark){ s.addText(runs,{x:M,y:0.72,w:12.1,h:1.0,isTextBox:true,margin:0,
  fontFace:HF,fontSize:32,bold:true,color:dark?WHITE:INK,lineSpacingMultiple:1.02}); }
function card(s,x,y,w,h,dark,fillOver,tr){ s.addShape(p.ShapeType.roundRect,{x,y,w,h,
  rectRadius:0.09, fill:{color:fillOver||(dark?NAVY2:CARD),transparency:tr==null?0:tr},
  line:{color:dark?"243B52":CARDLINE,width:1}}); }
function arrow(s,x1,y1,x2,y2,color){ s.addShape(p.ShapeType.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,
  line:{color:color||MUTED,width:2.5,endArrowType:"triangle"}}); }

// ===== Slide 1: タイトル（溢水画像フルブリード） =====
(function(){ const s=slide(NAVY);
  cover(s,HERO,0,0,SW,SH);
  scrim(s,0,0,SW,SH,"081320",40);
  scrim(s,0,0,7.6,SH,"081320",25);
  s.addText("OTセキュリティ入門ハンズオン",{x:M,y:1.1,w:7,h:0.4,isTextBox:true,margin:0,
    fontFace:HF,fontSize:13,bold:true,color:CYBR,charSpacing:3});
  s.addText([
    {text:"産業用通信 ",options:{color:WHITE}},
    {text:"Modbus",options:{color:CYBR}},
    {text:" で\n制御装置を乗っ取る",options:{color:WHITE}},
  ],{x:M,y:1.7,w:7.2,h:2.2,isTextBox:true,margin:0,fontFace:HF,fontSize:42,bold:true,
    lineSpacingMultiple:1.05,shadow:{type:"outer",color:"000000",opacity:0.5,blur:6,offset:2,angle:90}});
  s.addText("認証のない制御通信を使って、水のタンクを実際にあふれさせるまでを体験します。",
    {x:M,y:4.2,w:6.7,h:1.0,isTextBox:true,margin:0,fontFace:BF,fontSize:17,color:MUTED_D,lineSpacingMultiple:1.2});
  s.addText("前半 10分 基礎説明   ／   後半 50分 演習（CTF形式）",
    {x:M,y:6.7,w:9,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:13,color:"9DB1C6"});
  s.addNotes("導入。産業用プロトコルModbusで制御装置を乗っ取り、タンクをあふれさせる攻撃を自分の手で体験する。前半10分で基礎、後半50分で演習。");
})();

// ===== Slide 2: ゴール（結論先頭・ダーク） =====
(function(){ const s=slide(NAVY);
  eyebrow(s,"今日のゴール",true);
  s.addText([
    {text:"攻撃を自分の手で体験し、\n",options:{color:WHITE}},
    {text:"なぜ防げないのか",options:{color:CYBR}},
    {text:"を理解する",options:{color:WHITE}},
  ],{x:M,y:1.3,w:12,h:1.7,isTextBox:true,margin:0,fontFace:HF,fontSize:36,bold:true,lineSpacingMultiple:1.05});
  card(s,M,3.3,12.1,1.2,true,"102033");
  s.addText([
    {text:"やること:  ",options:{bold:true,color:WHITE}},
    {text:"認証のない産業用通信を使って、タンクを",options:{color:WHITE}},
    {text:"あふれさせる",options:{bold:true,color:"FF8DA1"}},
    {text:"。",options:{color:WHITE}},
  ],{x:M+0.3,y:3.3,w:11.5,h:1.2,isTextBox:true,margin:0,valign:"middle",fontFace:BF,fontSize:21});
  const items=[
    ["攻撃対象","貯液タンクの水位を自動制御する制御装置（PLC）のシミュレータ"],
    ["設計図は渡さない","どの番号が何を表すかは、読み書きしながら自分で解き明かす"],
    ["最後に","「どう防ぐか」をみんなで考える"],
  ];
  items.forEach((it,i)=>{ const y=4.9+i*0.72;
    s.addShape(p.ShapeType.ellipse,{x:M,y:y+0.05,w:0.18,h:0.18,fill:{color:CYBR},line:{type:"none"}});
    s.addText([{text:it[0]+"  ",options:{bold:true,color:WHITE}},{text:it[1],options:{color:MUTED_D}}],
      {x:M+0.4,y:y-0.08,w:11.5,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:16});
  });
  s.addNotes("結論を先に。目的は『なぜ防げないか』を理解すること。対象はPLCシミュレータ。設計図は渡さず自分で解く。最後に防御を議論する。");
})();

// ===== Slide 3: 制御の仕組み（制御盤画像） =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"まず、制御の仕組み");
  title(s,"制御装置（PLC）がタンクの水位を自動で保つ");
  cover(s,ROOM,7.0,1.95,5.75,4.9);
  s.addText([
    {text:"制御装置（PLC）は、タンクの水位を読み、給水ポンプをオン・オフして水位を一定に保ちます。",
      options:{breakLine:true,color:INK}},
    {text:" ",options:{breakLine:true,fontSize:8}},
    {text:"・停止水位",options:{bold:true,color:CY}},
    {text:"に達したらポンプを止め、低い水位で動かす。",options:{color:INK,breakLine:true}},
    {text:"・安全インターロック",options:{bold:true,color:CY}},
    {text:"：危険域でポンプを強制停止する「最後の砦」。",options:{color:INK}},
  ],{x:M,y:2.4,w:6.0,h:4.0,isTextBox:true,margin:0,fontFace:BF,fontSize:18,lineSpacingMultiple:1.4});
  s.addText("後半では、この制御装置そのものを攻撃します。",
    {x:M,y:6.1,w:6.0,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:14,italic:true,color:MUTED});
  s.addNotes("制御の基本。PLCが水位を読みポンプをオンオフして水位を保つ。停止水位と、危険域で止める安全インターロックの二重の守り。これが攻撃対象になる。");
})();

// ===== Slide 4: Modbusとは（データモデル・クリーン） =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"通信のことば");
  title(s,"Modbus — 産業機器の事実上の標準プロトコル");
  const ly=2.9;
  card(s,0.9,ly,2.7,1.5);
  s.addText("攻撃者\n/ 監視端末",{x:0.9,y:ly,w:2.7,h:1.5,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:15,bold:true,color:INK});
  card(s,5.0,ly,2.7,1.5);
  s.addText("制御装置",{x:5.0,y:ly,w:2.7,h:1.5,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:15,bold:true,color:INK});
  arrow(s,3.6,ly+0.55,5.0,ly+0.55,CY);
  s.addText("「○番を読め / 書け」",{x:3.3,y:ly+0.12,w:2.0,h:0.3,isTextBox:true,align:"center",fontFace:BF,fontSize:10,color:MUTED});
  arrow(s,5.0,ly+1.05,3.6,ly+1.05,MUTED);
  s.addText("値を返す",{x:3.3,y:ly+1.08,w:2.0,h:0.3,isTextBox:true,align:"center",fontFace:BF,fontSize:10,color:MUTED});
  card(s,8.2,2.5,4.5,3.2);
  s.addText("データの持ち方",{x:8.5,y:2.7,w:4,h:0.4,isTextBox:true,fontFace:BF,fontSize:15,bold:true,color:CY});
  s.addText([
    {text:"コイル",options:{bold:true,color:INK}},
    {text:" = オン/オフの1ビット（例: ポンプ）",options:{color:INK,breakLine:true}},
    {text:"レジスタ",options:{bold:true,color:INK}},
    {text:" = 16ビットの数値（例: 水位・設定値）",options:{color:INK,breakLine:true}},
    {text:" ",options:{breakLine:true,fontSize:8}},
    {text:"番号付きの「記憶の棚」を読み書きするだけ。",options:{color:MUTED}},
  ],{x:8.5,y:3.2,w:4.0,h:2.2,isTextBox:true,margin:0,fontFace:BF,fontSize:15,lineSpacingMultiple:1.35});
  s.addText([{text:"ポート: ",options:{color:MUTED}},{text:"502（今回は 5020）",options:{bold:true,color:CY}}],
    {x:8.5,y:5.05,w:4,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:14});
  s.addNotes("Modbusは産業の標準。依頼側が『何番を読め/書け』と送り機器が答えるだけ。データはコイル(オンオフ)とレジスタ(数値)。ポートは502、今回は5020。");
})();

// ===== Slide 5: 3つの欠陥（施錠破り画像フルブリード） =====
(function(){ const s=slide(NAVY);
  cover(s,LOCK,0,0,SW,SH);
  scrim(s,0,0,SW,SH,"070E18",52);
  s.addText("ここが弱点".toUpperCase(),{x:M,y:0.42,w:12,h:0.3,isTextBox:true,margin:0,
    fontFace:HF,fontSize:12,bold:true,color:CYBR,charSpacing:3});
  s.addText("Modbus には 3つの構造的な欠陥がある",{x:M,y:0.72,w:12.1,h:1.0,isTextBox:true,margin:0,
    fontFace:HF,fontSize:32,bold:true,color:WHITE});
  const flaws=[
    ["認証なし","相手が誰かを確かめない。到達できれば誰でも書ける。"],
    ["暗号化なし","通信は平文。覗けば、値も命令も丸見え。"],
    ["改ざん検知なし","正しい命令かを検証しない。偽の命令も実行する。"],
  ];
  const cw=3.85, gap=0.3, x0=M, y=2.4, ch=2.5;
  flaws.forEach((f,i)=>{ const x=x0+i*(cw+gap);
    s.addShape(p.ShapeType.roundRect,{x,y,w:cw,h:ch,rectRadius:0.09,
      fill:{color:"0C1826",transparency:12},line:{color:"3A2130",width:1}});
    s.addText(f[0],{x:x+0.3,y:y+0.35,w:cw-0.6,h:0.7,isTextBox:true,margin:0,fontFace:HF,fontSize:23,bold:true,color:"FF7A8E"});
    s.addText(f[1],{x:x+0.3,y:y+1.25,w:cw-0.6,h:1.1,isTextBox:true,margin:0,fontFace:BF,fontSize:15,color:"D7E2EE",lineSpacingMultiple:1.3});
  });
  s.addText([
    {text:"つまり、",options:{color:WHITE}},
    {text:"ネットワークに入れた時点で、制御を好きに書き換えられる。",options:{bold:true,color:CYBR}},
  ],{x:M,y:5.45,w:12.1,h:0.9,isTextBox:true,margin:0,fontFace:BF,fontSize:20,align:"center",valign:"middle"});
  s.addNotes("Modbusの致命的な3欠陥：認証なし・暗号化なし・改ざん検知なし。ネットワークに到達できた時点で制御を好きに書き換えられる。");
})();

// ===== Slide 6: 読める・書ける・落とせる =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"欠陥が何を招くか");
  title(s,"読める・書ける・落とせる");
  const rows=[
    ["読める",CY,"盗聴・偵察","水位も設定値も丸見え。工場の中身を把握される。","機密"],
    ["書ける",DANGER,"改ざん","設定値を書き換え、安全装置を無効化 → 物理被害（溢水）。","完全性"],
    ["落とせる",MUTED,"妨害","不正な値や大量接続で動作を乱す。","可用性"],
  ];
  rows.forEach((r,i)=>{ const y=2.55+i*1.25;
    s.addShape(p.ShapeType.roundRect,{x:M,y:y,w:2.1,h:0.7,rectRadius:0.35,fill:{color:r[1]},line:{type:"none"}});
    s.addText(r[0],{x:M,y:y,w:2.1,h:0.7,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:18,bold:true,color:WHITE});
    arrow(s,2.95,y+0.35,3.5,y+0.35,MUTED);
    s.addText([{text:r[2]+"  ",options:{bold:true,color:INK}},{text:r[3],options:{color:INK}}],
      {x:3.7,y:y-0.05,w:7.6,h:0.8,isTextBox:true,margin:0,valign:"middle",fontFace:BF,fontSize:16,lineSpacingMultiple:1.15});
    s.addText(r[4],{x:11.4,y:y,w:1.3,h:0.7,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:13,bold:true,color:r[1]});
  });
  s.addText("情報セキュリティの3要素（機密・完全性・可用性）が、そのまま崩れます。",
    {x:M,y:6.45,w:12,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:14,color:MUTED});
  s.addNotes("3欠陥は被害に直結。読める＝盗聴(機密)、書ける＝改ざんで物理被害(完全性)、落とせる＝妨害(可用性)。CIAがそのまま崩れる。");
})();

// ===== Slide 7: 演習の流れ =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"演習の流れ（CTF形式）");
  title(s,"偵察から始め、最後はタンクをあふれさせる");
  const steps=["1 偵察","2 盗聴","3 ポンプ奪取","4 設定改ざん","5 安全無効化","6 溢水"];
  const n=steps.length, x0=M, y=2.8, totalW=12.1, sw=1.72, gap=(totalW-sw*n)/(n-1);
  steps.forEach((t,i)=>{ const x=x0+i*(sw+gap); const last=i===n-1;
    s.addShape(p.ShapeType.roundRect,{x,y,w:sw,h:1.0,rectRadius:0.14,
      fill:{color:last?DANGER:CARD},line:{color:last?DANGER:CARDLINE,width:1}});
    s.addText(t,{x:x,y:y,w:sw,h:1.0,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:14,bold:true,color:last?WHITE:INK});
    if(!last){ const ax=x+sw+gap*0.15; s.addText("→",{x:ax,y:y,w:gap*0.7,h:1.0,isTextBox:true,align:"center",valign:"middle",fontFace:BF,fontSize:18,color:MUTED}); }
  });
  s.addText("目的達成",{x:x0+5*(sw+gap),y:y+1.02,w:sw,h:0.3,isTextBox:true,align:"center",fontFace:BF,fontSize:11,bold:true,color:DANGER});
  s.addText([
    {text:"攻撃に成功すると、制御装置が",options:{color:INK}},
    {text:"フラグ",options:{bold:true,color:CY}},
    {text:"をレジスタに出します。読み出して提出。",options:{color:INK,breakLine:true}},
    {text:"設計図は渡しません。",options:{color:INK}},
    {text:"観測して自分で当てる",options:{bold:true,color:INK}},
    {text:" のがこの演習の面白さです。",options:{color:INK}},
  ],{x:M,y:4.5,w:12,h:1.5,isTextBox:true,margin:0,fontFace:BF,fontSize:17,lineSpacingMultiple:1.35});
  s.addNotes("CTF形式。偵察→盗聴→ポンプ奪取→設定改ざん→安全無効化→溢水。成功するとフラグがレジスタに出るので読んで提出。設計図は渡さず自分で当てる。");
})();

// ===== Slide 8: ルール =====
(function(){ const s=slide(PAPER);
  eyebrow(s,"始める前に");
  title(s,"ルールと安全");
  card(s,M,2.6,12.1,1.6,false,"FBECEE");
  s.addText("本編は AI 禁止",{x:M+0.4,y:2.8,w:11,h:0.6,isTextBox:true,margin:0,fontFace:HF,fontSize:24,bold:true,color:DANGER});
  s.addText("レジスタの意味を推定してあふれさせる部分は、自分で読み解くのが目的です。Wireshark の使い方や Modbus 全般の調べ物に AI を使うのは構いません。",
    {x:M+0.4,y:3.4,w:11.3,h:0.7,isTextBox:true,margin:0,fontFace:BF,fontSize:15,color:INK,lineSpacingMultiple:1.25});
  const bl=[
    "詰まったら遠慮なく、司会にヒントを求めてください。",
    "これは隔離されたネットワーク専用の演習です。渡された制御装置以外には接続しません。",
  ];
  bl.forEach((t,i)=>{ const y=4.7+i*0.7;
    s.addShape(p.ShapeType.ellipse,{x:M,y:y+0.08,w:0.18,h:0.18,fill:{color:CY},line:{type:"none"}});
    s.addText(t,{x:M+0.4,y:y-0.08,w:11.5,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:16,color:INK});
  });
  s.addNotes("本編はAI禁止（自分で読み解くのが目的。Wireshark等の調べ物は可）。詰まったら司会にヒントを。隔離ネット専用で渡した制御装置以外には触らない。");
})();

// ===== Slide 9: 開始（溢水画像フルブリード・CTA） =====
(function(){ const s=slide(NAVY);
  cover(s,HERO,0,0,SW,SH);
  scrim(s,0,0,SW,SH,"081320",55);
  s.addText("さあ、始めましょう".toUpperCase(),{x:M,y:0.6,w:12,h:0.3,isTextBox:true,margin:0,
    fontFace:HF,fontSize:12,bold:true,color:CYBR,charSpacing:3});
  s.addText("接続して、制御装置を読んでみる",{x:M,y:0.95,w:12.1,h:1.0,isTextBox:true,margin:0,
    fontFace:HF,fontSize:32,bold:true,color:WHITE});
  card(s,M,2.5,5.9,1.5,true,"0E2033",10);
  s.addText("問題とフラグ提出（CTFd）",{x:M+0.35,y:2.75,w:5.2,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:15,bold:true,color:WHITE});
  s.addText("http://<司会のIP>:8000",{x:M+0.35,y:3.25,w:5.2,h:0.5,isTextBox:true,margin:0,fontFace:HF,fontSize:19,bold:true,color:CYBR});
  card(s,M+6.2,2.5,5.9,1.5,true,"0E2033",10);
  s.addText("制御装置（攻撃対象）",{x:M+6.55,y:2.75,w:5.2,h:0.4,isTextBox:true,margin:0,fontFace:BF,fontSize:15,bold:true,color:WHITE});
  s.addText("<司会のIP>:5020",{x:M+6.55,y:3.25,w:5.2,h:0.5,isTextBox:true,margin:0,fontFace:HF,fontSize:19,bold:true,color:CYBR});
  s.addText("配布キットの mbclient.py で、まずは保持レジスタを読んでみましょう。",
    {x:M,y:4.5,w:12,h:0.5,isTextBox:true,margin:0,fontFace:BF,fontSize:18,color:MUTED_D});
  s.addShape(p.ShapeType.roundRect,{x:M,y:5.2,w:12.1,h:0.95,rectRadius:0.06,fill:{color:"05101C",transparency:8},line:{color:"24384F",width:1}});
  s.addText("python3 mbclient.py --host <IP> read-hr 0 30",
    {x:M+0.3,y:5.2,w:11.5,h:0.95,isTextBox:true,margin:0,valign:"middle",fontFace:"Courier New",fontSize:17,color:"7BE3B0"});
  s.addNotes("さあ接続。CTFdは司会のIP:8000、制御装置は:5020。まずmbclientで保持レジスタを読む。ここから演習(偵察)に入る。");
})();

const OUT = process.env.OUT || "ot-intro.pptx";
p.writeFile({ fileName: OUT }).then(f=>console.log("wrote",f));
