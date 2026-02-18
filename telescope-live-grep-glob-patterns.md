# Using Glob Patterns (-g) with Telescope.nvim Live Grep

## Interactive Glob Input in Telescope Prompt

You want to type the glob pattern directly in the Telescope prompt window. Here are your options:

---

## Option 1: Prompt for Glob Pattern BEFORE Opening Telescope

```lua
vim.keymap.set('n', '<leader>fg', function()
  vim.ui.input({ prompt = 'Glob pattern (e.g. *.lua): ' }, function(pattern)
    if pattern then
      require('telescope.builtin').live_grep({
        glob_pattern = pattern
      })
    else
      -- No pattern entered, search all files
      require('telescope.builtin').live_grep()
    end
  end)
end, { desc = 'Live grep with glob prompt' })
```

---

## Option 2: Use telescope-live-grep-args Extension (RECOMMENDED)

This extension allows you to type rg arguments directly in the telescope prompt!

### Installation (lazy.nvim)

```lua
{
  "nvim-telescope/telescope-live-grep-args.nvim",
  dependencies = { "nvim-telescope/telescope.nvim" },
  config = function()
    require("telescope").load_extension("live_grep_args")
  end,
}
```

### Usage

```lua
vim.keymap.set('n', '<leader>fg', function()
  require('telescope').extensions.live_grep_args.live_grep_args()
end, { desc = 'Live grep with args' })
```

### In the Prompt Window You Can Type:

```
search_term -g *.lua
search_term --glob=*.py
search_term -t rust
"exact phrase" -g !*_test.*
```

---

## Option 3: Custom Live Grep with Prompt Parsing

Create your own live_grep that parses `-g` from the prompt:

```lua
local function live_grep_with_args()
  local pickers = require('telescope.pickers')
  local finders = require('telescope.finders')
  local conf = require('telescope.config').values
  local make_entry = require('telescope.make_entry')

  local function parse_prompt(prompt)
    -- Parse: "search_term -g *.lua" or "search_term --glob=*.lua"
    local search = prompt
    local globs = {}

    -- Extract -g patterns
    for glob in prompt:gmatch('%-g%s+([^%s]+)') do
      table.insert(globs, '--glob=' .. glob)
      search = search:gsub('%-g%s+' .. vim.pesc(glob), '')
    end

    -- Extract --glob= patterns
    for glob in prompt:gmatch('%-%-glob=([^%s]+)') do
      table.insert(globs, '--glob=' .. glob)
      search = search:gsub('%-%-glob=' .. vim.pesc(glob), '')
    end

    search = vim.trim(search)
    return search, globs
  end

  local vimgrep_args = vim.deepcopy(conf.vimgrep_arguments)

  local live_grepper = finders.new_job(function(prompt)
    if not prompt or prompt == '' then return nil end

    local search, globs = parse_prompt(prompt)
    if search == '' then return nil end

    local args = vim.list_extend(vim.deepcopy(vimgrep_args), globs)
    table.insert(args, '--')
    table.insert(args, search)
    return args
  end, make_entry.gen_from_vimgrep({}))

  pickers.new({}, {
    prompt_title = 'Live Grep (use -g *.ext)',
    finder = live_grepper,
    previewer = conf.grep_previewer({}),
    sorter = require('telescope.sorters').highlighter_only({}),
  }):find()
end

vim.keymap.set('n', '<leader>fg', live_grep_with_args, { desc = 'Live grep with -g support' })
```

**Usage in prompt:** `my_function -g *.lua` or `TODO -g !*_test.py`

---

## Option 4: Multiple Keymaps for Common Patterns

```lua
-- General live grep
vim.keymap.set('n', '<leader>fg', require('telescope.builtin').live_grep)

-- Lua files only
vim.keymap.set('n', '<leader>fgl', function()
  require('telescope.builtin').live_grep({ glob_pattern = '*.lua' })
end, { desc = 'Grep Lua files' })

-- Python files only
vim.keymap.set('n', '<leader>fgp', function()
  require('telescope.builtin').live_grep({ glob_pattern = '*.py' })
end, { desc = 'Grep Python files' })

-- Exclude tests
vim.keymap.set('n', '<leader>fgs', function()
  require('telescope.builtin').live_grep({ glob_pattern = { '!*_test.*', '!*_spec.*' } })
end, { desc = 'Grep excluding tests' })
```

---

## Quick Reference

| Method | Pros | Cons |
|--------|------|------|
| `vim.ui.input` prompt | Simple, no dependencies | Extra popup before telescope |
| `telescope-live-grep-args` | Full rg args in prompt | Requires extension |
| Custom parser | No dependencies, inline | More code to maintain |
| Multiple keymaps | Fast, no typing | Need to remember keymaps |

