import React, { useEffect, useMemo, useState } from "react";

function daysBetween(a, b) {
  const ms = Math.abs(new Date(a).getTime() - new Date(b).getTime());
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

export default function LawTracker() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [process, setProcess] = useState("all");
  const [action, setAction] = useState("all");

  useEffect(() => {
    fetch("/data/items.json", { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => setItems(Array.isArray(j) ? j : []))
      .catch(() => setItems([]));
  }, []);

  const filtered = useMemo(() => {
    const qq = q.trim();
    const now = new Date().toISOString().slice(0, 10);

    const scored = items
      .filter((it) => {
        if (!it) return false;
        if (process !== "all" && it.process !== process) return false;
        if (action !== "all" && it.action !== action) return false;
        if (!qq) return true;
        const blob = [
          it.title,
          it.topic,
          it.law_family,
          ...(it.summary_3 || []),
          ...(it.target || []),
          ...(it.tags || []),
        ]
          .filter(Boolean)
          .join(" ");
        return blob.includes(qq);
      })
      .map((it) => {
        const act = it.action || "WATCH";
        const actScore = act === "ACT_NOW" ? 4 : act === "PREPARE" ? 3 : act === "WATCH" ? 2 : 1;
        const updated = it.updated_at || now;
        const recency = 100 - Math.min(100, daysBetween(updated, now));
        return { it, score: actScore * 1000 + recency };
      })
      .sort((a, b) => b.score - a.score)
      .map((x) => x.it);

    return scored;
  }, [items, q, process, action]);

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: 16 }}>
      <h2 style={{ fontSize: 22, marginBottom: 12 }}>法改正トラッカー（通知なし）</h2>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="検索（タイトル / 要点 / 対象 / タグ）"
          style={{ padding: 10, minWidth: 260, flex: "1 1 260px" }}
        />
        <select value={process} onChange={(e) => setProcess(e.target.value)} style={{ padding: 10 }}>
          <option value="all">process: 全部</option>
          <option value="policy">検討段階</option>
          <option value="public_comment">パブコメ</option>
          <option value="diet">国会審議中</option>
          <option value="promulgated">公布済み</option>
          <option value="enforcement_planned">施行予定</option>
          <option value="enforced">施行済み</option>
        </select>
        <select value={action} onChange={(e) => setAction(e.target.value)} style={{ padding: 10 }}>
          <option value="all">action: 全部</option>
          <option value="WATCH">WATCH</option>
          <option value="PREPARE">PREPARE</option>
          <option value="ACT_NOW">ACT NOW</option>
          <option value="CLOSE">CLOSE</option>
        </select>
      </div>

      {filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: 32, color: "#888" }}>
          該当する案件はありません
        </div>
      )}

      <div style={{ display: "grid", gap: 10 }}>
        {filtered.map((it) => (
          <div key={it.id} style={{ border: "1px solid #ddd", borderRadius: 10, padding: 12 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <strong style={{ fontSize: 16 }}>{it.title}</strong>
              <span style={{ fontSize: 12, padding: "2px 8px", border: "1px solid #ccc", borderRadius: 999 }}>
                {it.process}
              </span>
              <span style={{ fontSize: 12, padding: "2px 8px", border: "1px solid #ccc", borderRadius: 999 }}>
                {it.action}
              </span>
              {(it.tags || []).includes("needs_review") && (
                <span style={{ fontSize: 12, padding: "2px 8px", border: "1px solid #f1c40f", borderRadius: 999 }}>
                  needs_review
                </span>
              )}
              {(it.tags || []).includes("reviewed") && (
                <span style={{ fontSize: 12, padding: "2px 8px", border: "1px solid #2ecc71", borderRadius: 999 }}>
                  reviewed
                </span>
              )}
            </div>

            <div style={{ marginTop: 8, color: "#444" }}>
              {(it.summary_3 || []).filter(Boolean).slice(0, 3).map((s, i) => (
                <div key={i}>{"\u2022"} {s}</div>
              ))}
            </div>

            <div style={{ marginTop: 8, display: "flex", gap: 12, flexWrap: "wrap", fontSize: 13, color: "#666" }}>
              {(it.target || []).length > 0 && (
                <span>対象: {it.target.join(", ")}</span>
              )}
              {it.risk_if_delayed && (
                <span>遅延リスク: {it.risk_if_delayed}</span>
              )}
              {it.updated_at && (
                <span>更新: {it.updated_at}</span>
              )}
            </div>

            {(it.sources || []).length > 0 && (
              <div style={{ marginTop: 6, fontSize: 12 }}>
                {it.sources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ marginRight: 12, color: "#2563eb", textDecoration: "underline" }}
                  >
                    {src.label || "ソース"}
                  </a>
                ))}
              </div>
            )}

            {(it.actions || []).length > 0 && (
              <div style={{ marginTop: 6, fontSize: 13 }}>
                {it.actions.map((a, i) => (
                  <span key={i} style={{ marginRight: 12 }}>
                    [{a.owner}] {a.text}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
