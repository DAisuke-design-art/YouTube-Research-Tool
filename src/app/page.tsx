'use client';

import { useState, useMemo } from 'react';
import { Search, Loader2, Youtube, Calendar, Eye, ThumbsUp, MessageSquare, Users, CalendarDays, Download, ArrowUpDown, TrendingUp, BarChart3 } from 'lucide-react';
import { VideoItem } from '@/types/youtube';
import DatePicker, { registerLocale } from 'react-datepicker';
import { ja } from 'date-fns/locale';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { exportData } from '@/lib/export';

registerLocale('ja', ja);

export default function Home() {
  const [query, setQuery] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [results, setResults] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [lastQuery, setLastQuery] = useState('');
  const [videoType, setVideoType] = useState<'any' | 'normal' | 'shorts'>('normal');
  const [displayFilter, setDisplayFilter] = useState<'all' | 'normal' | 'shorts' | 'over-subscribers'>('all');
  const [sortKey, setSortKey] = useState<'date' | 'views' | 'likes' | 'comments'>('views');
  const [channelId, setChannelId] = useState('');
  const [videoComments, setVideoComments] = useState<Record<string, any[]>>({});
  const [loadingComments, setLoadingComments] = useState<Record<string, boolean>>({});

  // ソート・ローカルフィルタ済み結果をメモ化
  const sortedResults = useMemo(() => {
    if (results.length === 0) return [];

    // ローカルフィルタリング
    const filtered = results.filter(item => {
      if (displayFilter === 'all') return true;

      let isShort = false;
      if (item.duration) {
        const match = item.duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
        if (match) {
          const hours = parseInt(match[1] || '0', 10);
          const minutes = parseInt(match[2] || '0', 10);
          const seconds = parseInt(match[3] || '0', 10);
          const totalSeconds = hours * 3600 + minutes * 60 + seconds;
          isShort = totalSeconds <= 60;
        }
      }

      if (displayFilter === 'normal') return !isShort;
      if (displayFilter === 'shorts') return isShort;
      if (displayFilter === 'over-subscribers') return item.viewCount > item.subscriberCount;
      return true;
    });

    return [...filtered].sort((a, b) => {
      switch (sortKey) {
        case 'date':
          return b.publishedAt.localeCompare(a.publishedAt);
        case 'views':
          return b.viewCount - a.viewCount;
        case 'likes':
          return b.likeCount - a.likeCount;
        case 'comments':
          return b.commentCount - a.commentCount;
        default:
          return 0;
      }
    });
  }, [results, sortKey, displayFilter]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setShowExportMenu(false);
    setDisplayFilter('all'); // 検索実行時は全表示タブに戻す

    try {
      let apiUrl = `/api/search?q=${encodeURIComponent(query)}&videoType=${videoType}`;
      if (startDate) {
        apiUrl += `&startDate=${format(startDate, 'yyyy-MM-dd')}`;
      }
      if (endDate) {
        apiUrl += `&endDate=${format(endDate, 'yyyy-MM-dd')}`;
      }
      if (channelId.trim()) {
        apiUrl += `&channelId=${encodeURIComponent(channelId.trim())}`;
      }

      const response = await fetch(apiUrl);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || '検索中にエラーが発生しました');
      }

      setResults(data.results);
      setLastQuery(query);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    await exportData(sortedResults, 'xlsx', lastQuery, videoComments);
  };

  const handleFetchComments = async (videoId: string) => {
    setLoadingComments(prev => ({ ...prev, [videoId]: true }));
    try {
      const response = await fetch(`/api/comments?videoId=${videoId}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setVideoComments(prev => ({ ...prev, [videoId]: data.comments }));
    } catch (err: any) {
      console.error('Comment fetch error:', err);
    } finally {
      setLoadingComments(prev => ({ ...prev, [videoId]: false }));
    }
  };

  const handleExportSingleVideo = async (video: VideoItem) => {
    try {
      const singleComments: Record<string, any[]> = {};
      if (videoComments[video.videoId]) {
        singleComments[video.videoId] = videoComments[video.videoId];
      }
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: [video], keyword: lastQuery, comments: singleComments }),
      });
      if (!response.ok) return;
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${video.channelTitle}_${video.videoId}.xlsx`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { document.body.removeChild(a); window.URL.revokeObjectURL(url); }, 100);
    } catch (err: any) {
      console.error('Single export error:', err);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ja-JP').format(num);
  };

  return (
    <main className="min-h-screen bg-neutral-900 text-gray-200 pb-20 selection:bg-red-500/30">
      {/* Header */}
      <header className="bg-neutral-900/80 backdrop-blur-xl border-b border-white/10 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Youtube className="w-9 h-9 text-red-500" />
              <h1 className="text-2xl font-black tracking-tight text-white">
                YouTube Research Tool V2
              </h1>
              <span className="ml-3 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/20">
                JP Only
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
        {/* Search Section */}
        <div className="bg-neutral-800 rounded-3xl shadow-xl border border-white/5 p-8 mb-12">
          <form onSubmit={handleSearch} className="max-w-3xl mx-auto flex flex-col gap-6">

            <div className="flex flex-col gap-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-400 ml-1">
                検索キーワード <span className="text-red-500">*</span>
              </label>
              <div className="relative flex items-center group">
                <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-500 group-focus-within:text-red-400 transition-colors" />
                </div>
                <input
                  type="text"
                  id="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="例: AI Gemini, n8n Youtube"
                  className="block w-full bg-neutral-900 text-white rounded-2xl border-2 border-transparent shadow-inner focus:border-red-500/50 focus:bg-neutral-800/80 focus:ring-4 focus:ring-red-500/10 py-4 pl-12 pr-6 text-lg transition-all outline-none placeholder:text-gray-500"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex flex-col gap-2">
                <label className="block text-sm font-medium text-gray-400 ml-1 flex items-center gap-2">
                  <CalendarDays className="w-4 h-4" />
                  期間フィルター（開始日）
                </label>
                <div className="relative">
                  <DatePicker
                    selected={startDate}
                    onChange={(date: Date | null) => setStartDate(date)}
                    selectsStart
                    startDate={startDate}
                    endDate={endDate}
                    locale="ja"
                    dateFormat="yyyy/MM/dd"
                    placeholderText="年/月/日"
                    isClearable
                    className="block w-full bg-neutral-900 text-white rounded-xl border border-white/10 shadow-inner focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 py-3 px-4 transition-all outline-none placeholder:text-gray-600"
                    wrapperClassName="w-full"
                    calendarClassName="!bg-neutral-800 !border-white/10 !text-white !font-sans !shadow-2xl"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="block text-sm font-medium text-gray-400 ml-1 flex items-center gap-2">
                  <CalendarDays className="w-4 h-4" />
                  期間フィルター（終了日）
                </label>
                <div className="relative">
                  <DatePicker
                    selected={endDate}
                    onChange={(date: Date | null) => setEndDate(date)}
                    selectsEnd
                    startDate={startDate}
                    endDate={endDate}
                    minDate={startDate || undefined}
                    locale="ja"
                    dateFormat="yyyy/MM/dd"
                    placeholderText="年/月/日"
                    isClearable
                    className="block w-full bg-neutral-900 text-white rounded-xl border border-white/10 shadow-inner focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 py-3 px-4 transition-all outline-none placeholder:text-gray-600"
                    wrapperClassName="w-full"
                    calendarClassName="!bg-neutral-800 !border-white/10 !text-white !font-sans !shadow-2xl"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <label className="block text-sm font-medium text-gray-400 ml-1 flex items-center gap-2">
                  <Youtube className="w-4 h-4" />
                  動画タイプ
                </label>
                <select
                  value={videoType}
                  onChange={(e) => setVideoType(e.target.value as 'any' | 'normal' | 'shorts')}
                  className="block w-full bg-neutral-900 text-white rounded-xl border border-white/10 shadow-inner focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 py-3 px-4 transition-all outline-none appearance-none"
                  style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%236b7280\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'%3E%3C/path%3E%3C/svg%3E")', backgroundPosition: 'right 1rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.5em 1.5em' }}
                >
                  <option value="normal">通常動画のみ（ショート除外）</option>
                  <option value="any">すべての動画（ショート含む）</option>
                  <option value="shorts">ショート動画のみ</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="block text-sm font-medium text-gray-400 ml-1 flex items-center gap-2">
                <Users className="w-4 h-4" />
                チャンネルID（任意）
              </label>
              <input
                type="text"
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                placeholder="例: UCxxxxxxxxxxxxxxxx"
                className="block w-full bg-neutral-900 text-white rounded-xl border border-white/10 shadow-inner focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 py-3 px-4 transition-all outline-none placeholder:text-gray-600 font-mono text-sm"
                disabled={loading}
              />
              <p className="text-[10px] text-gray-500 ml-1">指定するとそのチャンネル内の動画に絞り込みます</p>
            </div>

            <div className="pt-4 flex justify-center">
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-8 py-4 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl flex items-center transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100 shadow-lg shadow-red-900/20 text-lg w-full md:w-auto min-w-[200px] justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin mr-3" />
                    リサーチ実行中...
                  </>
                ) : (
                  'リサーチ実行'
                )}
              </button>
            </div>

            <p className="mt-2 text-xs font-medium text-gray-500 text-center">
              ※英数字のみのキーワードでも、厳密な言語・地域フィルタリングにより日本国内の人気上位動画のみを抽出します。
            </p>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 p-4 mb-8 rounded-2xl flex items-center text-red-200">
            <div className="w-2 h-2 rounded-full bg-red-500 shrink-0 mr-3 animate-pulse" />
            <p>{error}</p>
          </div>
        )}

        {/* Results Section */}
        {results.length > 0 && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col gap-4 border-b border-white/10 pb-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center">
                    検索結果
                    <span className="ml-3 px-3 py-1 rounded-full text-xs font-bold bg-white/10 text-white">
                      {sortedResults.length} 件
                    </span>
                  </h2>
                  <div className="text-xs font-mono text-gray-400 mt-2">
                    調査日時: {results[0].researchDate}
                  </div>
                </div>

                <button
                  onClick={handleExport}
                  className="flex items-center px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm font-medium text-gray-200 rounded-lg border border-white/10 transition-colors"
                >
                  <Download className="w-4 h-4 mr-2 text-gray-400" />
                  Excel出力
                </button>
              </div>

              {/* ローカルフィルタ（表示切り替え）タブ */}
              <div className="flex bg-neutral-900 border border-white/10 rounded-xl p-1 w-full sm:w-max overflow-x-auto mx-auto sm:mx-0">
                <button
                  onClick={() => setDisplayFilter('all')}
                  className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${displayFilter === 'all'
                    ? 'bg-neutral-800 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-neutral-800/50'
                    }`}
                >
                  すべての結果
                </button>
                <button
                  onClick={() => setDisplayFilter('normal')}
                  className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${displayFilter === 'normal'
                    ? 'bg-neutral-800 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-neutral-800/50'
                    }`}
                >
                  通常動画
                </button>
                <button
                  onClick={() => setDisplayFilter('shorts')}
                  className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${displayFilter === 'shorts'
                    ? 'bg-neutral-800 text-white shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-neutral-800/50'
                    }`}
                >
                  ショート動画
                </button>
                <button
                  onClick={() => setDisplayFilter('over-subscribers')}
                  className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap flex items-center justify-center gap-1.5 ${displayFilter === 'over-subscribers'
                    ? 'bg-red-500/20 text-red-100 shadow-sm border border-red-500/30'
                    : 'text-gray-400 hover:text-red-300 hover:bg-red-500/10'
                    }`}
                >
                  <span className="text-xs">🔥</span> 登録者超え
                </button>
              </div>

              {/* ソート切り替えボタン */}
              <div className="flex items-center gap-2 flex-wrap">
                <ArrowUpDown className="w-4 h-4 text-gray-500 mr-1" />
                {[
                  { key: 'date' as const, label: '最新', icon: Calendar },
                  { key: 'views' as const, label: '再生回数', icon: Eye },
                  { key: 'likes' as const, label: '高評価数', icon: ThumbsUp },
                  { key: 'comments' as const, label: 'コメント', icon: MessageSquare },
                ].map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setSortKey(key)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${sortKey === key
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : 'bg-neutral-800 text-gray-400 border border-white/5 hover:bg-neutral-700 hover:text-gray-200'
                      }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {sortedResults.map((video) => (
                <a
                  key={video.videoId}
                  href={video.videoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group bg-neutral-800 rounded-2xl border border-white/5 overflow-hidden hover:border-white/10 hover:shadow-xl hover:shadow-black/50 transition-all duration-300 flex flex-col relative"
                >
                  <div className="relative aspect-video w-full overflow-hidden bg-neutral-900">
                    <div className="absolute inset-0 bg-gradient-to-t from-neutral-800 via-transparent to-transparent opacity-80 z-10" />
                    <img
                      src={video.thumbnailUrl}
                      alt={video.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>
                  <div className="p-6 flex-1 flex flex-col relative z-20 -mt-6">
                    <h3 className="font-bold text-lg leading-snug mb-2 line-clamp-2 text-white group-hover:text-red-400 transition-colors drop-shadow-md">
                      {video.title}
                    </h3>

                    {video.viewCount > video.subscriberCount && (
                      <div className="mb-4 flex items-center">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-red-500/20 to-orange-500/20 text-red-300 border border-red-500/30 shadow-sm">
                          <span className="text-[10px]">🔥</span> 登録者数超えヒット
                        </span>
                      </div>
                    )}

                    <div className="flex items-center text-gray-400 mb-6 text-sm mt-auto">
                      <div className="w-8 h-8 rounded-full bg-neutral-700 flex items-center justify-center mr-3 shrink-0 border border-white/5">
                        <Users className="w-4 h-4 text-gray-300" />
                      </div>
                      <div className="truncate">
                        <p className="font-medium text-gray-200 truncate">{video.channelTitle}</p>
                        <p className="text-xs text-gray-400 mt-0.5">登録者数: {formatNumber(video.subscriberCount)}人</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm text-gray-400">
                      <div className="flex items-center bg-neutral-900/50 rounded-xl p-3 border border-white/5">
                        <Eye className="w-4 h-4 mr-2.5 text-blue-400 shrink-0" />
                        <span className="font-medium text-gray-200 truncate">{formatNumber(video.viewCount)}</span>
                      </div>
                      <div className="flex items-center bg-neutral-900/50 rounded-xl p-3 border border-white/5">
                        <Calendar className="w-4 h-4 mr-2.5 text-green-400 shrink-0" />
                        <span className="font-medium text-gray-200 truncate">{video.publishedAt}</span>
                      </div>
                      <div className="flex items-center bg-neutral-900/50 rounded-xl p-3 border border-white/5">
                        <ThumbsUp className="w-4 h-4 mr-2.5 text-red-400 shrink-0" />
                        <span className="font-medium text-gray-200 truncate">{formatNumber(video.likeCount)}</span>
                      </div>
                      <div className="flex items-center bg-neutral-900/50 rounded-xl p-3 border border-white/5">
                        <MessageSquare className="w-4 h-4 mr-2.5 text-yellow-500 shrink-0" />
                        <span className="font-medium text-gray-200 truncate">{formatNumber(video.commentCount)}</span>
                      </div>
                    </div>

                    {/* 分析指標 */}
                    <div className="grid grid-cols-2 gap-2 mt-3 text-xs text-gray-400">
                      <div className="flex items-center bg-emerald-500/5 rounded-lg px-2.5 py-2 border border-emerald-500/10">
                        <TrendingUp className="w-3.5 h-3.5 mr-2 text-emerald-400 shrink-0" />
                        <div className="truncate">
                          <span className="text-gray-500">高評価率 </span>
                          <span className="font-medium text-emerald-300">{(video.likeRate * 100).toFixed(2)}%</span>
                        </div>
                      </div>
                      <div className="flex items-center bg-amber-500/5 rounded-lg px-2.5 py-2 border border-amber-500/10">
                        <BarChart3 className="w-3.5 h-3.5 mr-2 text-amber-400 shrink-0" />
                        <div className="truncate">
                          <span className="text-gray-500">V/S比 </span>
                          <span className="font-medium text-amber-300">{video.viewSubRatio.toFixed(1)}x</span>
                        </div>
                      </div>
                      <div className="flex items-center bg-purple-500/5 rounded-lg px-2.5 py-2 border border-purple-500/10">
                        <MessageSquare className="w-3.5 h-3.5 mr-2 text-purple-400 shrink-0" />
                        <div className="truncate">
                          <span className="text-gray-500">コメ率 </span>
                          <span className="font-medium text-purple-300">{(video.commentRate * 100).toFixed(3)}%</span>
                        </div>
                      </div>
                      <div className="flex items-center bg-cyan-500/5 rounded-lg px-2.5 py-2 border border-cyan-500/10">
                        <Eye className="w-3.5 h-3.5 mr-2 text-cyan-400 shrink-0" />
                        <div className="truncate">
                          <span className="text-gray-500">日平均 </span>
                          <span className="font-medium text-cyan-300">{formatNumber(Math.round(video.dailyAvgViews))}</span>
                        </div>
                      </div>
                    </div>

                    {/* コメント抽出ボタン */}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleFetchComments(video.videoId);
                      }}
                      disabled={loadingComments[video.videoId] || !!videoComments[video.videoId]}
                      className={`mt-3 w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all ${videoComments[video.videoId]
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20 cursor-default'
                        : loadingComments[video.videoId]
                          ? 'bg-neutral-700 text-gray-400 border border-white/5 cursor-wait'
                          : 'bg-neutral-900/50 text-gray-400 border border-white/5 hover:bg-neutral-700 hover:text-white'
                        }`}
                    >
                      {videoComments[video.videoId] ? (
                        <><MessageSquare className="w-3.5 h-3.5" /> 抽出済 ({videoComments[video.videoId].reduce((a: number, t: any) => a + 1 + (t.replies?.length || 0), 0)}件)</>
                      ) : loadingComments[video.videoId] ? (
                        <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 抽出中...</>
                      ) : (
                        <><MessageSquare className="w-3.5 h-3.5" /> コメント抽出</>
                      )}
                    </button>

                    {/* 単体Excelダウンロード（コメント抽出済みのみ） */}
                    {videoComments[video.videoId] && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleExportSingleVideo(video);
                        }}
                        className="mt-1.5 w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium bg-neutral-900/50 text-gray-400 border border-white/5 hover:bg-indigo-500/10 hover:text-indigo-300 hover:border-indigo-500/20 transition-all"
                      >
                        <Download className="w-3.5 h-3.5" /> この動画のExcelを出力
                      </button>
                    )}

                    {/* 運営者返信率（コメント抽出済みの場合のみ表示） */}
                    {videoComments[video.videoId] && (() => {
                      const threads = videoComments[video.videoId];
                      let totalComments = 0;
                      let ownerComments = 0;
                      threads.forEach((t: any) => {
                        totalComments += 1 + (t.replies?.length || 0);
                        if (t.topLevelComment?.authorChannelId === video.channelId) ownerComments++;
                        (t.replies || []).forEach((r: any) => {
                          if (r.authorChannelId === video.channelId) ownerComments++;
                        });
                      });
                      const viewerComments = totalComments - ownerComments;
                      const ownerRatio = totalComments > 0 ? (ownerComments / totalComments * 100) : 0;

                      return (
                        <div className="mt-2 flex items-center gap-2 text-[11px]">
                          {ownerComments > 0 ? (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-500/10 text-blue-300 border border-blue-500/20">
                              <Users className="w-3 h-3" />
                              運営返信 {ownerComments}件 ({ownerRatio.toFixed(1)}%) / 視聴者 {viewerComments}件
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-neutral-800 text-gray-500 border border-white/5">
                              運営返信なし / 視聴者 {viewerComments}件
                            </span>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {!loading && !error && results.length === 0 && query && (
          <div className="text-center py-24 bg-neutral-800 rounded-3xl border border-white/5">
            <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-300 mb-2">動画が見つかりませんでした</h3>
            <p className="text-gray-500 text-sm">日本国内の条件に一致する動画がありませんでした。</p>
          </div>
        )}
      </div>
    </main>
  );
}
