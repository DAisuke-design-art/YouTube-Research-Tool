import { VideoItem } from '@/types/youtube';

export function filterDomesticVideos(items: readonly VideoItem[]): VideoItem[] {
  return items.filter(item => {
    const rawDesc = (item as any)._rawDescription || '';
    const country = item.channelCountry;

    // 1. (Country == "JP") → 無条件で合格
    if (country === 'JP') {
      return true;
    }

    // 2. (Country が "JP" 以外の国コードが存在する) → 除外 ("US", "IN" など)
    if (country && country !== 'JP') {
      return false;
    }

    // 3. (Country が未設定 null/undefined 等)
    // タイトル または 説明文 に 平仮名/カタカナ が一部でも含まれれば日本向けと判定
    const combinedText = item.title + ' ' + rawDesc;
    
    // 平仮名 [\u3040-\u309F] or カタカナ [\u30A0-\u30FF] 
    const japaneseCharRegex = /[\u3040-\u309F\u30A0-\u30FF]/;
    if (japaneseCharRegex.test(combinedText)) {
      return true;
    }

    // 4. ELSE → 除外
    return false;
  }).map(item => {
    // 内部処理用のプロパティを掃除
    const cleanItem = { ...item };
    delete (cleanItem as any)._rawDescription;
    return cleanItem;
  });
}
