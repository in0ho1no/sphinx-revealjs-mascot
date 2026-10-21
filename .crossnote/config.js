// Crossnote / Markdown Preview Enhanced の表示・変換設定。
({
  katexConfig: {
  "macros": {}
},
  
  mathjaxConfig: {
  "tex": {},
  "options": {},
  "loader": {}
},
  
  mermaidConfig: {
  "startOnLoad": false
},

  // 数式の区切り記号を $ … $ と $$ … $$ だけにする。
  // 既定では \( … \) もインライン数式、\[ … \] もブロック数式になるため、
  // 括弧をエスケープした \(注\) や \[更新\] のような記述が数式として表示されてしまう。
  mathInlineDelimiters: [
    ["$", "$"]
  ],
  mathBlockDelimiters: [
    ["$$", "$$"]
  ],
})
