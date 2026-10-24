import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dist=path.join(root,'dist-full');

fs.rmSync(dist,{recursive:true,force:true});
fs.mkdirSync(dist,{recursive:true});
for(const name of ['index.html','styles.css','app.js','engine.js','bank-config.js','combine.js','assets','data']){
  fs.cpSync(path.join(root,name),path.join(dist,name),{recursive:true});
}
fs.writeFileSync(path.join(dist,'.nojekyll'),'');
console.log(`Full static folder created at ${dist}`);
