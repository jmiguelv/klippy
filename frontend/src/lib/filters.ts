/**
 * Metadata fields available across indexed documents.
 * Update this list when new fields are added to the YAML frontmatter schema.
 * Run GET /debug/fields against the backend to discover current fields.
 */
export const KNOWN_FIELDS = [
	'assignees', 'author', 'created_at', 'creator', 'date', 'doc_name',
	'folder', 'header_path', 'id', 'list', 'repo', 'sha', 'source',
	'space', 'status', 'type', 'updated_at', 'url', 'workspace'
] as const;
