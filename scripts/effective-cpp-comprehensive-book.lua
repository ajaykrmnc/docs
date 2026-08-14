local stringify = pandoc.utils.stringify

local function para_markdown_header(block)
  if block.t ~= "Para" then
    return nil
  end

  local content_start = nil
  local level = nil

  for i, inline in ipairs(block.content) do
    if inline.t ~= "RawInline" and inline.t ~= "SoftBreak" and inline.t ~= "Space" then
      if inline.t == "Str" and inline.text:match("^#+$") then
        level = #inline.text
        content_start = i + 1
      end
      break
    end
  end

  if not level or level < 2 then
    return nil
  end

  local header_content = {}
  for i = content_start, #block.content do
    local inline = block.content[i]
    if not (i == content_start and inline.t == "Space") then
      table.insert(header_content, inline)
    end
  end

  return pandoc.Header(level - 1, header_content)
end

function Blocks(blocks)
  local result = {}
  local in_body = false

  for _, block in ipairs(blocks) do
    local normalized = para_markdown_header(block) or block

    if normalized.t == "Header" and stringify(normalized.content) == "Chapter 1: Accustoming Yourself to C++" then
      in_body = true
    end

    if in_body then
      if normalized.t == "Header" and normalized.level > 1 then
        normalized.level = normalized.level - 1
      end
      table.insert(result, normalized)
    end
  end

  return result
end
