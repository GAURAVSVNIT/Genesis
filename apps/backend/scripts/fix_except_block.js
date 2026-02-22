const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Processing ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');

// Target lines 0-indexed: 803 -> 802
// 803: except...
// 804-806: body...

if (lines[802].includes('except Exception as e:')) {
    lines[802] = '    except Exception as e:';
}
if (lines[803].includes('print(f"🔥 CRTICAL ERROR')) {
    lines[803] = '        print(f"🔥 CRTICAL ERROR in generate_content: {e}")';
}
if (lines[804].includes('print(traceback.format_exc())')) {
    lines[804] = '        print(traceback.format_exc())';
}
if (lines[805].includes('raise HTTPException')) {
    lines[805] = '        raise HTTPException(status_code=500, detail=str(e))';
}

fs.writeFileSync(filePath, lines.join('\n'));
console.log('Except block fixed.');
