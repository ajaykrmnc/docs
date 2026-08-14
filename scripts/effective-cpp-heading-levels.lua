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

function Header(header)
  if header.level == 1 and stringify(header.content):match("^Item%s+%d+:") then
    header.level = 2
  end

  return header
end
