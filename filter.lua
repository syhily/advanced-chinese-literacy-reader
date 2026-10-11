-- 《语文素养高级读本》pandoc Lua filter(精简版)。
-- 稿件已是 pandoc 原生 Markdown(标题层级/属性、fenced div、bracketed span),
-- 本 filter 只负责三件必须在语法树上完成的事:
--
--   1. `> 诗行`(单层 blockquote)  -> div.verse > LineBlock(行内换行保留;
--      相邻的诗节块合并为一个 verse, 整首诗按最长行收缩居中、共享左缘)
--   2. `>> 文字`(嵌套 blockquote) -> div.quote 引文块(每行一段;
--      相邻的引文块合并为一个, 避免框间出现空白行)
--   3. 段内软换行合并: 两侧均为 CJK 则相连, 一侧是 ASCII 字母数字则补一个空格
--      (blockquote 在第 1/2 步先行消耗软换行, 不受影响)
--   4. 正文书名号《…》统一标为 span.bt(楷体, 与拓展阅读指引一致)

local function is_ascii_alnum(cp)
  return (cp >= 48 and cp <= 57) or (cp >= 65 and cp <= 90) or (cp >= 97 and cp <= 122)
end
local function is_cjk(cp)
  return cp >= 0x4E00 and cp <= 0x9FFF
end
local function lastcp(s)
  return utf8.codepoint(s, utf8.offset(s, -1))
end
local function firstcp(s)
  return utf8.codepoint(s, 1)
end

local function join_inlines(inls)
  local res = {}
  for i, il in ipairs(inls) do
    if il.t == 'SoftBreak' then
      local prev, nxt = res[#res], inls[i + 1]
      local a = prev and prev.t == 'Str' and lastcp(prev.text) or nil
      local b = nxt and nxt.t == 'Str' and firstcp(nxt.text) or nil
      local space = a and b and
        ((is_ascii_alnum(a) and (is_ascii_alnum(b) or is_cjk(b)))
         or (is_cjk(a) and is_ascii_alnum(b)))
      if space then table.insert(res, pandoc.Space()) end
    else
      table.insert(res, il)
    end
  end
  return res
end

-- 按软换行切分行内元素(诗行/引文行)
local function split_lines(inls)
  local lines, cur = {}, {}
  for _, il in ipairs(inls) do
    if il.t == 'SoftBreak' or il.t == 'LineBreak' then
      table.insert(lines, cur); cur = {}
    else
      table.insert(cur, il)
    end
  end
  table.insert(lines, cur)
  return lines
end

-- 书名号《…》标为 span.bt(跨多个 Str/Space 时按状态机聚合; 不递归进已有 span)
local function mark_titles(inls)
  local res, buf = {}, {}
  local in_t = false
  local function flush()
    if #buf == 0 then return end
    if in_t then
      table.insert(res, pandoc.Span(buf, pandoc.Attr('', {'bt'})))
    else
      for _, x in ipairs(buf) do table.insert(res, x) end
    end
    buf = {}
  end
  for _, il in ipairs(inls) do
    if il.t == 'Str' then
      local s = il.text
      local pos = 1
      while pos <= #s do
        -- 书名号是多字节字符, 不能用 [《》] 字节类, 须逐个字面量查找
        local i1 = s:find('《', pos, true)
        local i2 = s:find('》', pos, true)
        local i, ch
        if i1 and (not i2 or i1 < i2) then i, ch = i1, '《'
        elseif i2 then i, ch = i2, '》'
        else break end
        if i > pos then table.insert(buf, pandoc.Str(s:sub(pos, i - 1))) end
        if ch == '《' then
          flush()
          in_t = true
          table.insert(buf, pandoc.Str('《'))
        else
          table.insert(buf, pandoc.Str('》'))
          flush()
          in_t = false
        end
        pos = i + 3
      end
      if pos <= #s then table.insert(buf, pandoc.Str(s:sub(pos))) end
    else
      table.insert(buf, il)  -- Space/Strong 等原样进入缓冲区
    end
  end
  flush()
  return res
end

local out = {}

-- 输出前统一做软换行合并; 若上一个输出块是同类 div(quote/verse)则合并
local function emit(class, blocks)
  local last = out[#out]
  if last and last.t == 'Div' and last.classes[1] == class then
    for _, b in ipairs(blocks) do table.insert(last.content, b) end
    return
  end
  local d = pandoc.Div(blocks, pandoc.Attr('', {class}))
  table.insert(out, pandoc.walk_block(d, {Inlines = join_inlines}))
end

local function on_blockquote(bq)
  local inner = bq.content
  if #inner == 1 and inner[1].t == 'BlockQuote' then
    -- >> 引文: 每行一段, 空段(全角空格)保留
    local paras = {}
    for _, blk in ipairs(inner[1].content) do
      if blk.t == 'Para' or blk.t == 'Plain' then
        for _, line in ipairs(split_lines(blk.content)) do
          if #line > 0 then table.insert(paras, pandoc.Para(mark_titles(line))) end
        end
      else
        table.insert(paras, blk)
      end
    end
    emit('quote', paras)
    return
  end
  -- > 诗行: 行内换行保留为 LineBlock, 空行分节
  local stanzas = {}
  for _, blk in ipairs(inner) do
    if blk.t == 'Para' or blk.t == 'Plain' then
      table.insert(stanzas, pandoc.LineBlock(split_lines(blk.content)))
    else
      table.insert(stanzas, blk)
    end
  end
  emit('verse', stanzas)
end

-- 递归给段落/标题/列表/脚注正文打书刊名标记(不递归进已有 span, 避免重复包裹)
local function transform_block(b)
  if b.t == 'Para' or b.t == 'Plain' or b.t == 'Header' then
    b.content = mark_titles(b.content)
  elseif b.t == 'Div' then
    for i, sub in ipairs(b.content) do b.content[i] = transform_block(sub) end
  elseif b.t == 'LineBlock' then
    for i, ln in ipairs(b.content) do b.content[i] = mark_titles(ln) end
  elseif b.t == 'OrderedList' or b.t == 'BulletList' then
    for _, item in ipairs(b.content) do
      for i, sub in ipairs(item) do item[i] = transform_block(sub) end
    end
  elseif b.t == 'Note' then
    for i, sub in ipairs(b.content) do b.content[i] = transform_block(sub) end
  end
  return b
end

function Pandoc(doc)
  for _, b in ipairs(doc.blocks) do
    if b.t == 'BlockQuote' then
      on_blockquote(b)
    else
      table.insert(out, pandoc.walk_block(transform_block(b), {Inlines = join_inlines}))
    end
  end
  return pandoc.Pandoc(out, doc.meta)
end
