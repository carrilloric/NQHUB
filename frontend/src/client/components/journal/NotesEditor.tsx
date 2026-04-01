/**
 * NotesEditor - Notes and tags editor with 1s debounce
 * AUT-356
 */
import { useState, useEffect, useRef } from 'react';

interface NotesEditorProps {
  tradeId?: string;
  initialNotes?: string;
  initialTags?: string[];
  onSave: (tradeId: string, notes: string, tags: string[]) => Promise<boolean>;
}

export function NotesEditor({ tradeId, initialNotes = '', initialTags = [], onSave }: NotesEditorProps) {
  const [notes, setNotes] = useState(initialNotes);
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>(initialTags);
  const [isSaving, setIsSaving] = useState(false);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Update when selected trade changes (only on tradeId change)
  useEffect(() => {
    setNotes(initialNotes);
    setTags(initialTags);
    setTagInput('');
  }, [tradeId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced save function
  const debouncedSave = (newNotes: string, newTags: string[]) => {
    if (!tradeId) return;

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(async () => {
      setIsSaving(true);
      await onSave(tradeId, newNotes, newTags);
      setIsSaving(false);
    }, 1000); // 1 second debounce
  };

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newNotes = e.target.value;
    setNotes(newNotes);
    debouncedSave(newNotes, tags);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      const newTags = [...tags, tagInput.trim()];
      setTags(newTags);
      setTagInput('');
      if (tradeId) {
        debouncedSave(notes, newTags);
      }
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const newTags = tags.filter((tag) => tag !== tagToRemove);
    setTags(newTags);
    if (tradeId) {
      debouncedSave(notes, newTags);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  if (!tradeId) {
    return (
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow text-center text-gray-500 dark:text-gray-400">
        Select a trade to add notes and tags
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Trade Notes
        </h3>
        {isSaving && (
          <span className="text-sm text-gray-500 dark:text-gray-400">Saving...</span>
        )}
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Notes
        </label>
        <textarea
          value={notes}
          onChange={handleNotesChange}
          onBlur={() => {
            // Force save on blur (test requirement)
            if (tradeId && debounceTimer.current) {
              clearTimeout(debounceTimer.current);
              setIsSaving(true);
              onSave(tradeId, notes, tags).finally(() => setIsSaving(false));
            }
          }}
          placeholder="Add notes about this trade..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Tags
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Add tag (press Enter)"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          <button
            onClick={handleAddTag}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium"
          >
            Add
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
            >
              {tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
