import React, { useState } from 'react';
import { Search, ExternalLink, Calendar, FileText, MessageSquare, CheckCircle, Clock, AlertCircle, RefreshCw, Download, Bell, HelpCircle } from 'lucide-react';

// 法令データ
const lawCategories = {
  "基本法": [
    { id: "roudoukijunhou", name: "労働基準法" },
    { id: "roudouanzeneisei", name: "労働安全衛生法" },
    { id: "roudoukeiyaku", name: "労働契約法" },
    { id: "jinhaihou", name: "じん肺法" }
  ],
  "施行令・規則": [
    { id: "roudouanzeneiseikisoku", name: "労働安全衛生規則" },
    { id: "boiler", name: "ボイラー及び圧力容器安全規則" },
    { id: "crane", name: "クレーン等安全規則" },
    { id: "tokutei", name: "特定化学物質障害予防規則" },
    { id: "sekimen", name: "石綿障害予防規則" }
  ]
};

// 改正プロセス
const revisionStages = [
  { 
    id: "consideration", 
    name: "検討段階", 
    icon: FileText, 
    bgClass: "bg-gray-100",
    textClass: "text-gray-600",
    borderColor: "#6b7280",
    description: "厚生労働省内や審議会で改正の必要性を検討している段階",
    detail: "労働政策審議会などで専門家による議論が行われます"
  },
  { 
    id: "public_comment", 
    name: "パブリックコメント", 
    icon: MessageSquare, 
    bgClass: "bg-blue-100",
    textClass: "text-blue-600",
    borderColor: "#3b82f6",
    description: "改正案について広く国民から意見を募集する期間",
    detail: "e-Govを通じて誰でも意見を提出できます"
  },
  { 
    id: "deliberation", 
    name: "国会審議中", 
    icon: FileText, 
    bgClass: "bg-yellow-100",
    textClass: "text-yellow-600",
    borderColor: "#eab308",
    description: "法案が国会に提出され、審議されている段階",
    detail: "委員会審議、本会議での採決を経て成立します"
  },
  { 
    id: "promulgated", 
    name: "公布済み", 
    icon: CheckCircle, 
    bgClass: "bg-green-100",
    textClass: "text-green-600",
    borderColor: "#22c55e",
    description: "法律が成立し、官報に掲載された段階",
    detail: "公布日から一定期間後に施行されます"
  },
  { 
    id: "enforcement_scheduled", 
    name: "施行予定", 
    icon: Clock, 
    bgClass: "bg-purple-100",
    textClass: "text-purple-600",
    borderColor: "#a855f7",
    description: "施行日が決まっている段階",
    detail: "企業は対応準備が必要です"
  },
  { 
    id: "enforced", 
    name: "施行済み", 
    icon: CheckCircle, 
    bgClass: "bg-gray-100",
    textClass: "text-gray-600",
    borderColor: "#6b7280",
    description: "法律が効力を発生している段階",
    detail: "企業は法令を遵守する義務があります"
  }
];

// サンプル改正情報
const sampleRevisions = [
  {
    id: 0,
    lawName: "労働安全衛生規則",
    title: "AI・ロボット技術の進展に伴う安全規制の在り方検討",
    stage: "consideration",
    description: "労働政策審議会安全衛生分科会で、AI・協働ロボット等の新技術に対応した安全基準の検討を開始",
    officialUrl: "https://www.mhlw.go.jp/stf/shingi/shingi-rousei_126969.html"
  },
  {
    id: 1,
    lawName: "労働安全衛生法及び作業環境測定法",
    title: "労働安全衛生法及び作業環境測定法の一部を改正する法律（令和7年法律第33号）",
    stage: "promulgated",
    promulgationDate: "2025-05-14",
    enforcementDate: "2026-04-01",
    description: "個人事業者等に対する安全衛生対策の推進、50人未満事業場でのストレスチェック義務化など",
    officialUrl: "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/an-eihou/index_00001.html",
    highlights: [
      "フリーランスへの安全衛生対策",
      "50人未満事業場でのストレスチェック義務化",
      "化学物質管理の強化"
    ]
  },
  {
    id: 2,
    lawName: "労働安全衛生規則",
    title: "労働安全衛生規則の一部改正（熱中症対策の強化）",
    stage: "enforced",
    promulgationDate: "2025-05-20",
    enforcementDate: "2025-06-01",
    description: "職場における熱中症対策の強化について、WBGT値に基づく予防措置の義務化",
    officialUrl: "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html"
  },
  {
    id: 3,
    lawName: "特定化学物質障害予防規則等",
    title: "化学物質による労働災害防止のための新たな規制",
    stage: "enforcement_scheduled",
    promulgationDate: "2024-02-24",
    enforcementDate: "2026-04-01",
    description: "ラベル表示・SDS交付義務対象物質の追加（約700物質追加、合計約1,600物質）",
    officialUrl: "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000099121_00005.html",
    highlights: [
      "2026年4月：さらに約850物質追加予定",
      "SDS交付義務違反への罰則新設",
      "化学物質管理者の選任義務"
    ]
  }
];

function SafetyLawTracker() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStage, setSelectedStage] = useState("all");
  const [showProcessDetails, setShowProcessDetails] = useState(false);
  const [expandedRevision, setExpandedRevision] = useState(null);

  const filteredRevisions = sampleRevisions.filter(revision => {
    const matchesSearch = revision.title.includes(searchTerm) || revision.description.includes(searchTerm);
    const matchesStage = selectedStage === "all" || revision.stage === selectedStage;
    return matchesSearch && matchesStage;
  });

  const getStageInfo = (stageId) => revisionStages.find(s => s.id === stageId);

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("ja-JP", { year: "numeric", month: "long", day: "numeric" });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-green-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold mb-2">労働安全衛生法令 改正追跡システム</h1>
          <p className="text-green-100">Safety Law Revision Tracker</p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* 重要なお知らせ */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex items-start">
            <Bell className="text-yellow-600 mr-3 mt-0.5" size={20} />
            <div>
              <h3 className="font-bold text-yellow-900 mb-1">重要な改正情報</h3>
              <p className="text-sm text-yellow-800">
                令和7年5月14日：労働安全衛生法及び作業環境測定法の一部改正法が公布されました
              </p>
            </div>
          </div>
        </div>

        {/* 検索・フィルター */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="法令名、改正内容で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="all">すべてのステージ</option>
              {revisionStages.map(stage => (
                <option key={stage.id} value={stage.id}>{stage.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* プロセスフロー */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold text-gray-800">法令改正プロセス</h2>
            <button
              onClick={() => setShowProcessDetails(!showProcessDetails)}
              className="flex items-center gap-2 px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
            >
              <HelpCircle size={16} />
              {showProcessDetails ? "説明を閉じる" : "各プロセスの説明を見る"}
            </button>
          </div>

          <div className="flex flex-wrap gap-3 mb-4">
            {revisionStages.map((stage, index) => {
              const Icon = stage.icon;
              const count = sampleRevisions.filter(r => r.stage === stage.id).length;
              return (
                <div key={stage.id} className="flex items-center">
                  <button
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                      selectedStage === stage.id 
                        ? "bg-green-100 border-2 border-green-500" 
                        : "bg-gray-100 border border-gray-300"
                    } cursor-pointer hover:shadow transition`}
                    onClick={() => setSelectedStage(selectedStage === stage.id ? "all" : stage.id)}
                  >
                    <Icon size={18} className={stage.textClass} />
                    <span className="font-medium text-sm">{stage.name}</span>
                    <span className="bg-white px-2 py-0.5 rounded-full text-xs font-bold">{count}</span>
                  </button>
                  {index < revisionStages.length - 1 && (
                    <div className="w-8 h-0.5 bg-gray-300 mx-1" />
                  )}
                </div>
              );
            })}
          </div>

          {showProcessDetails && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mt-4">
              <h3 className="font-bold text-blue-900 mb-3">各プロセスの説明</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {revisionStages.map(stage => {
                  const Icon = stage.icon;
                  return (
                    <div key={stage.id} className="bg-white rounded p-3 border border-blue-100">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon size={16} className={stage.textClass} />
                        <span className="font-bold text-sm text-gray-800">{stage.name}</span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{stage.description}</p>
                      <p className="text-xs text-gray-500 italic">{stage.detail}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* 改正情報リスト */}
        <div className="space-y-4 mb-8">
          {filteredRevisions.map(revision => {
            const stageInfo = getStageInfo(revision.stage);
            const StageIcon = stageInfo.icon;
            const isExpanded = expandedRevision === revision.id;

            return (
              <div key={revision.id} className="bg-white rounded-lg shadow hover:shadow-lg transition">
                <div 
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedRevision(isExpanded ? null : revision.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <StageIcon size={20} className={stageInfo.textClass} />
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${stageInfo.bgClass} ${stageInfo.textClass}`}>
                          {stageInfo.name}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-gray-800 mb-1">{revision.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{revision.lawName}</p>
                      <p className="text-gray-700">{revision.description}</p>
                      
                      {revision.highlights && revision.highlights.length > 0 && (
                        <div className="mt-3 bg-blue-50 rounded-lg p-3">
                          <p className="text-sm font-bold text-blue-900 mb-1">主なポイント：</p>
                          <ul className="text-sm text-blue-800 space-y-1">
                            {revision.highlights.map((highlight, idx) => (
                              <li key={idx}>• {highlight}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {revision.promulgationDate && (
                          <div className="flex items-center gap-2 text-sm">
                            <CheckCircle size={16} className="text-green-500" />
                            <span className="font-medium">公布日:</span>
                            <span>{formatDate(revision.promulgationDate)}</span>
                          </div>
                        )}
                        {revision.enforcementDate && (
                          <div className="flex items-center gap-2 text-sm">
                            <Clock size={16} className="text-purple-500" />
                            <span className="font-medium">施行日:</span>
                            <span className="font-bold">{formatDate(revision.enforcementDate)}</span>
                          </div>
                        )}
                      </div>
                      <a
                        href={revision.officialUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <FileText size={16} />
                        厚生労働省の公式ページ
                        <ExternalLink size={14} />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 法令一覧 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-800">対象法令一覧</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(lawCategories).map(([category, laws]) => (
              <div key={category} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-bold text-green-700 mb-2 pb-2 border-b border-gray-200">{category}</h3>
                <ul className="space-y-1">
                  {laws.map(law => (
                    <li key={law.id} className="text-sm text-gray-700">• {law.name}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SafetyLawTracker;
