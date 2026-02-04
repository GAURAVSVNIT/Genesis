const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Processing ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');

// 0-indexed
const tryIdx = 440; // Line 441

if (lines[tryIdx].trim().startsWith("try:")) {
    console.log("Removing try at line 441");
    // Remove the line
    lines.splice(tryIdx, 1);
} else {
    console.log("WARN: Line 441 is not try: " + lines[tryIdx]);
}

// Indent lines 414-440 (which are now indices 413 to 439?)
// Wait, if I splice at 440, indices < 440 are unchanged.
// Indices > 440 shift down.
// Range to indent: 413 to 439 (inclusive).
const startIndent = 413; // Line 414
const endIndent = 439;   // Line 440 (Print... Passed)

for (let i = startIndent; i <= endIndent; i++) {
    if (lines[i].trim().length > 0) {
        lines[i] = '    ' + lines[i];
    }
}

fs.writeFileSync(filePath, lines.join('\n'));
console.log('Merged try block.');
