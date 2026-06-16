-- File: resolve-ids.lua
-- This filter resolves alternate citation keys in a CSL-JSON bibliography file to their primary engine-readable IDs.
-- note that it requires the bibliography to be in CSL-JSON format, not BibTeX or other formats.
-- also it needs to be run before the --citeproc filter so that the citations are resolved before pandoc processes them.
local json = require 'pandoc.json'
local id_map = {}

local function trim(s)
    return string.match(s, "^%s*(.-)%s*$")
end

-- 1. Read and parse the JSON bibliography file to build our key lookup map
function Meta(meta)
  -- Safely extract the bibliography file path from metadata
  local bib_file = meta.bibliography and pandoc.utils.stringify(meta.bibliography)

  if not bib_file then
    io.stderr:write("Warning: No 'bibliography' metadata field found. Skip mapping.\n")
    return nil
  end

  -- Open and read the bibliography file
  local file = io.open(bib_file, "r")
  if not file then
    io.stderr:write("Warning: Could not open bibliography file: " .. bib_file .. "\n")
    return nil
  end

  local content = file:read("*all")
  file:close()

  -- Decode the JSON contents
  local success, bib_data = pcall(json.decode, content)
  if not success or type(bib_data) ~= "table" then
    io.stderr:write("Error: Bibliography file must be valid CSL-JSON.\n")
    return nil
  end

  -- Populate map: alternate-id -> primary-id
  for _, entry in ipairs(bib_data) do
    if entry.id and entry['other-ids'] then
      for  alt_id in string.gmatch(entry['other-ids'], "([^,]+)") do
        id_map[trim(alt_id)] = entry.id
      end
    end
  end
end

-- 2. Scan every citation block in the document and replace keys if a match is found
function Cite(cite)
  for _, citation in ipairs(cite.citations) do
    if id_map[citation.id] then
      -- Swap out the alternate ID for the primary engine-readable ID
      citation.id = id_map[citation.id]
    end
  end
  return cite
end

-- Ensure Meta runs before Cite to properly build the mapping database first
return {
  { Meta = Meta },
  { Cite = Cite }
}
