local function replace_status_symbols(text)
  return text:gsub("✅", "[GOOD]"):gsub("❌", "[BAD]")
end

function Str(inline)
  inline.text = replace_status_symbols(inline.text)
  return inline
end

function Code(inline)
  inline.text = replace_status_symbols(inline.text)
  return inline
end

function CodeBlock(block)
  block.text = replace_status_symbols(block.text)
  return block
end
