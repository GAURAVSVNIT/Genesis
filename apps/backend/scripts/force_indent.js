const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Processing ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');

// Target lines 0-indexed: 414 -> 802
// 1-indexed: 415 -> 803
// The try block content starts around 414/415.
// The except line is at 803 (which should be 4 spaces).
// So content is up to 802.

const startIdx = 413; // Line 414
const endIdx = 802;   // Line 803 (exclusive? no, lines[802] is line 803).
// Wait, 803 is 'except'. lines[802] is '    except'.
// So I should stop BEFORE 802.
// The content ends at 802 (line 803).
// The last line of content is 801 (line 802).
// So loop until 801.

for (let i = startIdx; i < endIdx; i++) {
    const line = lines[i];
    if (line.trim().length > 0) {
        // Force 8 spaces
        lines[i] = '        ' + line.trim();
    } else {
        // Keep empty lines empty (or just empty string)
        lines[i] = '';
    }
}

// Also ensure 'except' is 4 spaces
if (lines[endIdx].trim().startsWith('except')) {
   lines[endIdx] = '    ' + lines[endIdx].trim();
}

fs.writeFileSync(filePath, lines.join('\n'));
console.log('Indentation forced to 8 spaces.');
