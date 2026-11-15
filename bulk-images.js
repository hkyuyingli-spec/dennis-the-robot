const fs = require('fs');
const path = require('path');

const jsonPath = path.join(__dirname, 'frontend', 'src', 'data', 'herbal_kitchen.json');
const raw = fs.readFileSync(jsonPath, 'utf8').replace(/^\uFEFF/, '');
const data = JSON.parse(raw);
const dir = path.join(__dirname, 'frontend', 'public', 'images');
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

const HEADERS = { 'User-Agent': 'HerbalKitchenApp/1.0 (your-email@example.com)' };
const OVERRIDES = {
  sage: 'Salvia officinalis',
  tarragon: 'Artemisia dracunculus',
  cilantro: 'Coriander',
  coriander_seed: 'Coriander',
  clove: 'Syzygium aromaticum',
  black_pepper: 'Black pepper',
  paprika: 'Paprika',
  black_sesame: 'Sesame',
  white_sesame: 'Sesame',
  fingerroot: 'Boesenbergia rotunda',
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function politeFetch(url, tries = 5) {
  for (let i = 0; i < tries; i++) {
    const res = await fetch(url, { headers: HEADERS });
    if (res.status === 429 || res.status >= 500) {
      const wait = (Number(res.headers.get('retry-after')) || 5 * (i + 1)) * 1000;
      console.log(`   ⏳ HTTP ${res.status}, waiting ${wait / 1000}s...`);
      await sleep(wait);
      continue;
    }
    return res;
  }
  return null;
}

async function getWikiImage(term) {
  const url = `https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(term)}&gsrlimit=1&prop=pageimages&format=json&pithumbsize=500`;
  try {
    const res = await politeFetch(url);
    if (!res || !res.ok) { console.log(`   API failed: ${res ? res.status : 'no response'}`); return null; }
    const json = await res.json();
    const pages = json.query?.pages;
    if (!pages) return null;
    return Object.values(pages)[0].thumbnail?.source ?? null;
  } catch (e) { console.log(`   API error: ${e.message}`); return null; }
}

async function downloadImage(imageUrl, baseName) {
  try {
    const res = await politeFetch(imageUrl);
    if (!res || !res.ok) { console.log(`   Download failed: ${res ? res.status : 'no response'}`); return null; }
    const type = res.headers.get('content-type') || '';
    const ext = type.includes('png') ? 'png' : type.includes('webp') ? 'webp' : 'jpg';
    const file = `${baseName}.${ext}`;
    fs.writeFileSync(path.join(dir, file), Buffer.from(await res.arrayBuffer()));
    return file;
  } catch (e) { console.log(`   Download error: ${e.message}`); return null; }
}

async function run() {
  console.log('🚀 Starting bulk download...');
  let herbCount = 0, dishCount = 0;

  for (const herb of data.herbs) {
    if (herb.image && fs.existsSync(path.join(dir, path.basename(herb.image)))) {
      console.log(`⏭️  Already have: ${herb.names.en}`);
      continue;
    }

    const terms = [
      OVERRIDES[herb.id],
      herb.names.en.split('(')[0].trim(),
      herb.names.en.includes('(') ? herb.names.en.split('(')[1].replace(')', '').trim() : null,
      herb.names.id ? herb.names.id.split('(')[0].trim() : null,
      herb.id.replace(/_/g, ' ')
    ].filter(Boolean);

    let imageUrl = null;
    for (const t of [...new Set(terms)]) {
      imageUrl = await getWikiImage(t);
      await sleep(800);
      if (imageUrl) break;
    }

    if (imageUrl) {
      const file = await downloadImage(imageUrl, herb.id);
      await sleep(800);
      if (file) {
        herb.image = `/images/${file}`;
        herbCount++;
        console.log(`✅ ${herb.names.en}`);
        fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf8'); // save progress
        continue;
      }
    }
    console.log(`❌ No image found for: ${herb.names.en}`);
  }

  const herbById = Object.fromEntries(data.herbs.map(h => [h.id, h]));
  for (const dish of data.dishes) {
    const main = dish.ingredients?.[0] && herbById[dish.ingredients[0].herbId];
    if (main?.image) { dish.image = main.image; dishCount++; }
  }

  fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf8');
  console.log(`\n🎉 Done! New herb images: ${herbCount}, dishes linked: ${dishCount}`);
}

run();

