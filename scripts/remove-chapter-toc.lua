local function stringify(inlines)
  local parts = {}
  for _, inline in ipairs(inlines) do
    if inline.t == "Str" or inline.t == "Code" then
      table.insert(parts, inline.text)
    elseif inline.t == "Space" or inline.t == "SoftBreak" or inline.t == "LineBreak" then
      table.insert(parts, " ")
    end
  end
  return table.concat(parts)
end

function Blocks(blocks)
  local result = {}
  local skipping = false

  for _, block in ipairs(blocks) do
    if block.t == "Header" and block.level == 2 and stringify(block.content) == "Table of Contents" then
      skipping = true
    elseif skipping and block.t == "HorizontalRule" then
      skipping = false
    elseif not skipping then
      table.insert(result, block)
    end
  end

  return result
end
