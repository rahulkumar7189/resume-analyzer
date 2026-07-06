const fs = require('fs');
const file = 'd:/NLP/ats-web/src/app/recruiter/page.tsx';
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/className="([^"]*bg-primary[^"]*)text-foreground([^"]*)"/g, 'className="$1text-white$2"');
content = content.replace(/className="([^"]*bg-secondary[^"]*)text-foreground([^"]*)"/g, 'className="$1text-white$2"');

fs.writeFileSync(file, content);
console.log('Fixed button text colors!');
