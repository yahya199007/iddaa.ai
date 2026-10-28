// Global state
let allCouponsData = {};
let allMatchesData = [];
let activeCouponDay = 'net_guven';

document.addEventListener("DOMContentLoaded", () => {
    loadCoupons();
    loadMatches();
});

// Tab Switcher
function switchTab(tabName) {
    const tabs = ['coupons', 'matches', 'wizard'];
    tabs.forEach(t => {
        const sec = document.getElementById(`section-${t}`);
        const btn = document.getElementById(`tab-btn-${t}`);
        const mBtn = document.getElementById(`mobile-tab-${t}`);

        if (t === tabName) {
            if (sec) sec.classList.remove('hidden');
            if (btn) {
                btn.classList.add('active');
                btn.classList.remove('text-slate-400');
            }
            if (mBtn) {
                mBtn.classList.add('text-rose-500');
                mBtn.classList.remove('text-slate-400');
            }
        } else {
            if (sec) sec.classList.add('hidden');
            if (btn) {
                btn.classList.remove('active');
                btn.classList.add('text-slate-400');
            }
            if (mBtn) {
                mBtn.classList.remove('text-rose-500');
                mBtn.classList.add('text-slate-400');
            }
        }
    });
}

// Day Switcher for Coupons
function switchCouponDay(dayKey) {
    activeCouponDay = dayKey;
    const topBtns = ['net_guven', 'ust_25_net', 'kg_evet_net', 'kontrgaranti', 'today', 'tomorrow'];
    topBtns.forEach(b => {
        const btn = document.getElementById(`day-btn-${b}`);
        if (!btn) return;
        if (b === dayKey) {
            let activeClass = "bg-emerald-600";
            if (b === 'ust_25_net') activeClass = "bg-amber-600";
            else if (b === 'kg_evet_net') activeClass = "bg-teal-600";
            else if (b === 'kontrgaranti') activeClass = "bg-cyan-600";
            else if (b === 'today' || b === 'tomorrow') activeClass = "bg-blue-600";
            btn.className = `day-btn active px-3 sm:px-3.5 py-2 rounded-xl text-xs sm:text-sm font-black transition flex items-center space-x-1.5 ${activeClass} text-white shadow-md`;
        } else {
            btn.className = "day-btn px-3 sm:px-3.5 py-2 rounded-xl text-xs sm:text-sm font-bold transition flex items-center space-x-1.5 text-slate-300 hover:text-white";
        }
    });

    const extraBtns = ['aksam_300k', 'both_halves_kg', 'iy_ms_12_21', 'iy_ms_10_20', 'capa_skor_kombine', 'yuksek_oran_kg', 'iyms_sistem_56', 'skor_mbs1', 'iy_skor_sistem'];
    extraBtns.forEach(eb => {
        const eBtn = document.getElementById(`day-btn-${eb}`);
        if (!eBtn) return;
        if (eb === dayKey) {
            eBtn.className = "day-btn active px-2.5 py-1.5 rounded-lg text-xs font-bold transition bg-emerald-700 text-white border border-emerald-500 shadow-md";
        } else {
            eBtn.className = eb === 'aksam_300k'
                ? "day-btn px-2.5 py-1.5 rounded-lg text-xs font-bold transition text-amber-300 hover:text-white border border-amber-500/40 bg-amber-500/10"
                : "day-btn px-2.5 py-1.5 rounded-lg text-xs font-medium transition text-slate-300 hover:text-white";
        }
    });

    renderActiveCoupon();
}

// Toast Notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    const iconEl = document.getElementById('toast-icon');

    msgEl.textContent = message;
    if (isError) {
        iconEl.className = "fa-solid fa-triangle-exclamation text-rose-400 text-lg";
    } else {
        iconEl.className = "fa-solid fa-circle-check text-emerald-400 text-lg";
    }

    toast.classList.remove('translate-y-24', 'opacity-0');
    setTimeout(() => {
        toast.classList.add('translate-y-24', 'opacity-0');
    }, 3200);
}

// 1. Load Mega Coupons
async function loadCoupons() {
    const container = document.getElementById('coupon-display-container');
    container.innerHTML = `
        <div class="py-16 text-center text-slate-500">
            <i class="fa-solid fa-circle-notch fa-spin text-3xl mb-3 text-rose-500"></i>
            <p>Dünya futbolu taranıyor, takımların son 5 maçlık devre skorları inceleniyor...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/coupons');
        const data = await res.json();
        if (data.success) {
            allCouponsData = data.coupons;

            // Güncelleme: Buton etiketlerini tarihle doldur
            if (allCouponsData.today) {
                document.getElementById('label-today').textContent = allCouponsData.today.day_label || "Bugünün Kuponu";
            }
            if (allCouponsData.tomorrow) {
                document.getElementById('label-tomorrow').textContent = allCouponsData.tomorrow.day_label || "Yarının Kuponu";
            }

            renderActiveCoupon();
        } else {
            container.innerHTML = `<div class="py-12 text-center text-rose-400">Kuponlar yüklenemedi: ${data.error}</div>`;
        }
    } catch (err) {
        console.error(err);
        container.innerHTML = `<div class="py-12 text-center text-rose-400">Sunucu bağlantı hatası oluştu.</div>`;
    }
}

// Kısa analiz notu üretici (6 boyutlu kutular yerine tek satırlık özet not)
function getShortMatchNote(m) {
    if (m.short_note) return m.short_note;
    if (m.analysis_6d) {
        const parts = [];
        if (m.analysis_6d.form && m.analysis_6d.form.points && m.analysis_6d.form.points[0]) {
            parts.push(m.analysis_6d.form.points[0].replace(/^[^:]+:\s*/, ''));
        }
        if (m.analysis_6d.injuries && m.analysis_6d.injuries.points && m.analysis_6d.injuries.points[0]) {
            parts.push(m.analysis_6d.injuries.points[0].replace(/^[^:]+:\s*/, ''));
        }
        if (parts.length > 0) {
            const joined = parts.join(' ');
            return joined.length > 150 ? joined.slice(0, 147).trim() + '...' : joined;
        }
    }
    let raw = (m.deep_reason || m.last_5_summary || '').trim();
    raw = raw.replace(/^[^:]{3,35}\s*Analizi:\s*/i, '');
    const firstSentence = raw.split(/(?<=\.)\s+/)[0] || raw;
    return firstSentence.length > 145 ? firstSentence.slice(0, 142).trim() + '...' : firstSentence;
}

// Render Active Coupon - Güven odaklı net kart görünümü
function renderActiveCoupon() {
    const container = document.getElementById('coupon-display-container');
    const c = allCouponsData[activeCouponDay] || allCouponsData['net_guven'];

    if (!c) {
        container.innerHTML = `<div class="py-12 text-center text-slate-400">Bu sekme için kupon bulunamadı.</div>`;
        return;
    }

    const totalOddFormatted = c.total_odd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const stakeAmount = c.min_stake || 50;
    const isSystemCoupon = Boolean(c.system_label);
    const winAmount = isSystemCoupon && c.system_target_return
        ? Math.round(c.system_target_return)
        : Math.round(c.total_odd * stakeAmount);
    const winFormatted = winAmount.toLocaleString('tr-TR');
    const avgConf = Math.round(c.avg_confidence || 74);
    const isStandardModel = ['skor_mbs1', 'iy_skor_sistem', 'iyms_sistem_56', 'capa_skor_kombine', 'yuksek_oran_kg'].includes(c.type);

    // Pick badge renkleri
    function getPickBadgeStyle(pick) {
        const p = (pick || '').toLowerCase();
        if (p.includes('kontrgaranti') || p.includes('1x0') || p.includes('2x0') || p.includes('1x2')) return 'bg-cyan-600 text-white';
        if (p.includes('yarı skoru') || p.includes('maç skoru')) return 'bg-slate-700 text-white border border-slate-500';
        if (p.includes('2+ gol')) return 'bg-rose-600 text-white';
        if (p.includes('0/1') || p.includes('0/2')) return 'bg-indigo-600 text-white';
        if (p.includes('1/0') || p.includes('2/0') || p.includes('1/x')) return 'bg-orange-600 text-white';
        if (p.includes('1/2') || p.includes('2/1')) return 'bg-purple-600 text-white';
        if (p.includes('evet/evet') || p.includes('both_halves')) return 'bg-green-600 text-white';
        if (p.includes('ve kg var') || p.includes('ve 3,5')) return 'bg-amber-600 text-white';
        if (p.includes('karşılıklı gol') || p.includes('kg')) return 'bg-teal-600 text-white';
        if (p.includes('2,5 gol') || p.includes('üst')) return 'bg-amber-600 text-white';
        if (p.includes('maç sonucu')) return 'bg-emerald-600 text-white';
        return 'bg-slate-600 text-white';
    }

    // Nesine / İddaa tarzı Devre ve Maç Skoru (Skor & Tercih)
    function getPredictedScoreBadge(m) {
        if (m.nesine_score) return m.nesine_score;
        const p = (m.pick || '').toLowerCase();
        if (p.includes('1/2')) return '1-2 (İY: 1-0)';
        if (p.includes('2/1')) return '2-1 (İY: 0-1)';
        if (p.includes('0/1') || p.includes('x/1')) return '2-0 (İY: 0-0)';
        if (p.includes('0/2') || p.includes('x/2')) return '0-2 (İY: 0-0)';
        if (p.includes('1/0') || p.includes('1/x')) return '1-1 (İY: 1-0)';
        if (p.includes('2/0') || p.includes('2/x')) return '1-1 (İY: 0-1)';
        if (p.includes('1/1')) return '2-1 (İY: 1-0)';
        if (p.includes('2/2')) return '0-2 (İY: 0-1)';
        if (p.includes('evet/evet') || p.includes('both_halves')) return '2-2 (İY: 1-1)';
        if (p.includes('ve kg var')) return '2-1 (İY: 1-0)';
        if (p.includes('ve 3,5')) return '3-1 (İY: 2-0)';
        if (p.includes('maç sonucu: 1') || p.includes('ms 1')) return '2-0 (İY: 1-0)';
        if (p.includes('maç sonucu: 2') || p.includes('ms 2')) return '0-2 (İY: 0-1)';
        if (p.includes('2,5 gol: üst') || p.includes('2,5 üst')) return '2-1 (İY: 1-1)';
        if (p.includes('karşılıklı gol') || p.includes('kg')) return '1-1 (İY: 1-0)';
        return '2-0 (İY: 0-0)';
    }

    // Maç satırı oluştur
    let matchRowsHtml = '';
    c.matches.forEach((m) => {
        const pickStyle = getPickBadgeStyle(m.pick);
        const pickLabel = m.pick;
        const scoreBadge = getPredictedScoreBadge(m);
        const shortNote = getShortMatchNote(m);
        const confBadge = m.confidence_label || `%${Math.round(m.confidence || m.prob || 70)} Güven`;

        matchRowsHtml += `
        <div class="border-b border-slate-800/60 last:border-0">
            <!-- Maç Adı + Saat -->
            <div class="flex items-center justify-between px-1 pt-3 pb-1">
                <div>
                    <div class="font-black text-white text-sm sm:text-base">⚽ ${m.match_name}</div>
                    <div class="text-[11px] text-slate-400 mt-0.5">${m.league} • ${m.time}</div>
                </div>
                <div class="text-right">
                    <span class="text-[10px] text-slate-500 block">Bülten #${m.nesine_code || m.match_id}</span>
                </div>
            </div>
            <!-- Tahmin + Oran + Skor & Tercih + Güven -->
            <div class="flex items-center justify-between px-1 pb-2 gap-3 flex-wrap">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-3 py-1 rounded-lg text-xs font-black ${pickStyle} shadow-sm">${pickLabel}</span>
                    <span class="px-2 py-0.5 rounded-lg text-xs font-bold bg-slate-800 text-amber-300 border border-slate-700/80 shadow-sm" title="Nesine Devre ve Maç Skoru">📊 ${scoreBadge}</span>
                    <span class="font-mono font-black text-emerald-400 text-base">${m.odd.toFixed(2)}</span>
                    <span class="px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 text-[11px] font-bold">🛡️ ${confBadge}</span>
                </div>
                <!-- Tüm Platformlar Eşit Mini Bar -->
                <div class="flex items-center gap-1 overflow-x-auto text-[10px] font-bold">
                    <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">🇹🇷 İddaa ${m.odd.toFixed(2)}</span>
                    <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700/50">🟢 Nesine</span>
                    <span class="px-1.5 py-0.5 rounded bg-yellow-950 text-yellow-300 border border-yellow-700/50">🟡 Misli</span>
                    <span class="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-700/50 hidden sm:inline">🔵 Bilyoner</span>
                    <span class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700/50 hidden md:inline">🌐 Global ${(m.odd*1.04).toFixed(2)}</span>
                </div>
            </div>
            <!-- Kısa Analiz Notu -->
            <div class="px-1 pb-2.5 text-[11px] leading-snug flex items-start gap-1.5">
                <span class="text-amber-400 font-bold shrink-0">📝 Not:</span>
                <span class="text-slate-300">${shortNote}</span>
            </div>
        </div>`;
    });

    // Kupon tipi renkler
    let headerBg = 'from-emerald-900 via-emerald-800 to-teal-800';
    if (isStandardModel) headerBg = 'from-slate-800 via-slate-800 to-slate-900';
    else if (c.type === 'aksam_300k') headerBg = 'from-rose-900 via-pink-800 to-amber-800';
    else if (c.type === 'kontrgaranti') headerBg = 'from-cyan-900 via-sky-800 to-teal-800';
    else if (c.type === 'both_halves_kg') headerBg = 'from-green-900 via-emerald-800 to-teal-800';
    else if (c.type === 'iy_ms_10_20') headerBg = 'from-orange-900 via-amber-800 to-orange-800';
    else if (c.type === 'iy_ms_12_21') headerBg = 'from-purple-900 via-violet-800 to-indigo-800';
    else if (c.type === 'kg_evet_net') headerBg = 'from-teal-900 via-teal-800 to-cyan-800';
    else if (c.type === 'ust_25_net') headerBg = 'from-amber-900 via-amber-800 to-orange-800';
    else if (activeCouponDay === 'today' || activeCouponDay === 'tomorrow') headerBg = 'from-blue-900 via-indigo-800 to-slate-800';

    const winLabel = isStandardModel
        ? (isSystemCoupon ? `Sistem: ${c.system_label} • ${stakeAmount} TL` : `${stakeAmount} TL → ${winFormatted} TL`)
        : `🎯 ${stakeAmount} TL → ${winFormatted} TL Kazanç`;
    const oddHeaderTitle = isSystemCoupon ? 'ORT. ÇARPAN' : 'TOPLAM ORAN';
    const winFooterTitle = isSystemCoupon ? `Ort. Kazanç (${c.system_ref_hits || 4} İsabet)` : 'Tahmini Kazanç';
    const systemInfoBlock = isSystemCoupon
        ? `<div><span class="text-slate-400 text-xs">Sistem</span><div class="font-bold text-slate-200">${c.system_label}</div></div>`
        : '';

    // Hızlı geçiş mini kartları
    const allTypes = [
        { key:'net_guven', label:'Yüksek Güven Net (4 Maç)', icon:'fa-shield-halved', color:'emerald', oddKey:'net_guven' },
        { key:'ust_25_net', label:'4 Maç 2,5 Üst', icon:'fa-fire', color:'amber', oddKey:'ust_25_net' },
        { key:'kg_evet_net', label:'4 Maç KG Evet', icon:'fa-circle-check', color:'teal', oddKey:'kg_evet_net' },
        { key:'kontrgaranti', label:'Kontrgaranti ÇŞ (4 Maç)', icon:'fa-lock', color:'cyan', oddKey:'kontrgaranti' },
        { key:'today', label:'Bugün Net (4 Maç)', icon:'fa-calendar-check', color:'blue', oddKey:'today' },
        { key:'aksam_300k', label:'Kazanan 10 Hibrit (4 Maç)', icon:'fa-trophy', color:'rose', oddKey:'aksam_300k' },
        { key:'both_halves_kg', label:'4 Maç Evet/Evet', icon:'fa-futbol', color:'green', oddKey:'both_halves_kg' },
        { key:'iy_ms_12_21', label:'İY/MS 1/2 • 2/1 (4 Maç)', icon:'fa-rotate', color:'purple', oddKey:'iy_ms_12_21' },
        { key:'iy_ms_10_20', label:'İY/MS 1/0 • 2/0 (4 Maç)', icon:'fa-scale-balanced', color:'orange', oddKey:'iy_ms_10_20' },
        { key:'capa_skor_kombine', label:'Çapa + Dönüş (4 Maç)', icon:'fa-bullseye', color:'slate', oddKey:'capa_skor_kombine' },
        { key:'yuksek_oran_kg', label:'4 Maç Değer KG', icon:'fa-chart-simple', color:'teal', oddKey:'yuksek_oran_kg' },
    ];
    let navCardsHtml = '';
    allTypes.forEach(t => {
        const d = allCouponsData[t.oddKey];
        const oddVal = d ? (d.total_odd || 0).toLocaleString('tr-TR', {minimumFractionDigits:2, maximumFractionDigits:2}) : '-';
        const confVal = d && d.avg_confidence ? `%${Math.round(d.avg_confidence)}` : '';
        const isActive = activeCouponDay === t.key;
        navCardsHtml += `
        <button onclick="switchCouponDay('${t.key}')" class="text-left p-3 rounded-2xl border ${isActive ? `border-${t.color}-500 bg-${t.color}-500/15` : 'border-cardborder bg-cardbg hover:border-slate-600'} transition">
            <div class="text-[10px] text-${t.color}-300 font-bold uppercase flex items-center gap-1 mb-0.5">
                <i class="fa-solid ${t.icon} text-${t.color}-400"></i> ${t.label}
            </div>
            <div class="text-xs text-slate-400 font-mono flex items-center justify-between">
                <span>Oran: <strong class="text-${t.color}-400">${oddVal}</strong></span>
                <span class="text-[10px] text-emerald-400 font-bold">${confVal}</span>
            </div>
        </button>`;
    });

    container.innerHTML = `
    <div class="space-y-4">
        <div class="bg-[#0f1a14] border border-slate-700 rounded-2xl overflow-hidden shadow-2xl">

            <!-- Üst Başlık -->
            <div class="bg-gradient-to-r ${headerBg} px-5 py-4 flex items-center justify-between gap-3">
                <div>
                    <div class="flex items-center gap-2 mb-1 flex-wrap">
                        <span class="bg-emerald-400 text-slate-950 text-[11px] font-black px-2.5 py-0.5 rounded-full">${winLabel}</span>
                        <span class="bg-black/40 text-emerald-200 border border-emerald-400/40 text-[11px] font-black px-2.5 py-0.5 rounded-full">🛡️ Ort. Güven: %${avgConf}</span>
                    </div>
                    <div class="text-white font-black text-lg sm:text-xl">${c.title}</div>
                    <div class="text-white/75 text-xs mt-0.5">${c.badge}</div>
                </div>
                <div class="text-right bg-black/30 px-4 py-2 rounded-xl border border-white/10 shrink-0">
                    <div class="text-[10px] text-amber-200 uppercase font-bold">${oddHeaderTitle}</div>
                    <div class="text-2xl font-black font-mono text-white">${totalOddFormatted}</div>
                </div>
            </div>

            <!-- Maç Listesi -->
            <div class="px-4 sm:px-5 divide-y divide-slate-800/60">
                ${matchRowsHtml}
            </div>

            <!-- Alt Bilgi Çubuğu -->
            <div class="bg-[#0a1610] border-t border-slate-700 px-5 py-4">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div class="flex items-center gap-4 text-sm flex-wrap">
                        <div>
                            <span class="text-slate-400 text-xs">${isSystemCoupon ? 'Ort. Çarpan' : 'Toplam Oran'}</span>
                            <div class="font-black text-white font-mono">${totalOddFormatted}</div>
                        </div>
                        ${systemInfoBlock}
                        <div>
                            <span class="text-slate-400 text-xs">Kupon Tutarı</span>
                            <div class="font-black text-white">${stakeAmount} TL</div>
                        </div>
                        <div>
                            <span class="text-slate-400 text-xs">${winFooterTitle}</span>
                            <div class="font-black text-emerald-400 text-base">${winFormatted} TL</div>
                        </div>
                        <div>
                            <span class="text-slate-400 text-xs">Güven Ortalaması</span>
                            <div class="font-black text-amber-400">%${avgConf}</div>
                        </div>
                    </div>
                    <div class="flex gap-2 w-full sm:w-auto">
                        <button onclick="refreshAllCoupons()" id="coupon-card-refresh-btn" class="flex-1 sm:flex-none px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-black text-sm rounded-xl flex items-center justify-center gap-2 transition active:scale-95">
                            <i class="fa-solid fa-arrows-rotate" id="card-refresh-icon"></i>
                            <span>Güncelle</span>
                        </button>
                        <button onclick="copyCurrentCoupon()" class="flex-1 sm:flex-none px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white font-bold text-sm rounded-xl flex items-center justify-center gap-2 transition active:scale-95">
                            <i class="fa-solid fa-share-nodes"></i>
                            <span>Paylaş</span>
                        </button>
                    </div>
                </div>
                <div class="mt-3 text-[11px] text-slate-400 flex items-center gap-1.5">
                    <i class="fa-solid fa-circle-info text-emerald-500"></i>
                    <span>${c.summary}</span>
                </div>
            </div>
        </div>

        <!-- Hızlı Kupon Geçiş Kartları -->
        <div>
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                <i class="fa-solid fa-layer-group text-slate-500"></i>
                Güven Odaklı Kupon Seçenekleri
            </h4>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-2">
                ${navCardsHtml}
            </div>
        </div>
    </div>
    `;
}

// Copy Coupon Text
function copyCurrentCoupon() {
    const c = allCouponsData[activeCouponDay] || allCouponsData['net_guven'];
    if (!c) return;

    let text = `🛡️ *[İDDAA AI PRO - YÜKSEK GÜVENLİ ORTAK HAVUZ KUPONU]*\n`;
    text += `📌 Kupon: ${c.title}\n`;
    if (c.system_label) {
        text += `🔢 Sistem: ${c.system_label} (${c.min_stake} TL) | Ort. Kazanç (${c.system_ref_hits || 4} İsabet): ${Math.round(c.system_target_return || 0).toLocaleString('tr-TR')} TL\n`;
    } else {
        text += `📊 Toplam Oran: ${c.total_odd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} | Ort. Güven: %${Math.round(c.avg_confidence || 74)}\n`;
        text += `💰 Kupon Bedeli: ${c.min_stake || 50} TL → Kazanç: ${Math.round(c.total_odd * (c.min_stake || 50)).toLocaleString('tr-TR')} TL\n`;
    }
    text += `----------------------------------------------------\n`;
    c.matches.forEach((m, idx) => {
        const confTxt = m.confidence_label || `%${Math.round(m.confidence || 70)} Güven`;
        text += `${idx + 1}. ${m.match_name} (${m.time})\n`;
        text += `   ⚽ Tercih: ${m.pick} | Oran: ${m.odd.toFixed(2)} | 🛡️ ${confTxt}\n`;
        text += `   📝 Not: ${getShortMatchNote(m)}\n\n`;
    });
    text += `🤖 İddaa AI Pro (50+ Platform Ortak Oran Havuzu)`;

    navigator.clipboard.writeText(text).then(() => {
        showToast("✓ Kupon kopyalandı! Tüm platformlarda oynayabilirsiniz.");
    }).catch(() => {
        showToast("Kopyalama başarısız oldu.", true);
    });
}

// 2. Load World Matches Bulletin & Last 5 Matches History
async function loadMatches() {
    try {
        const res = await fetch('/api/matches');
        const data = await res.json();
        if (data.success) {
            allMatchesData = data.matches;
            const badge = document.getElementById('live-count-badge');
            if (badge) badge.textContent = `${data.matches.length} Maç`;
            renderBulletin(data.matches);
        }
    } catch (err) {
        console.error(err);
    }
}

let currentRotation = 0;

// Kuponları Canlı Olarak Güncelle ve Yeni Maç Kombinasyonları Üret
async function refreshAllCoupons() {
    const syncIcon = document.getElementById('sync-icon');
    const syncText = document.getElementById('sync-text');
    const syncBtn = document.getElementById('sync-nesine-btn');
    const cardIcon = document.getElementById('card-refresh-icon');
    const cardBtn = document.getElementById('coupon-card-refresh-btn');
    const mobileIcon = document.getElementById('mobile-refresh-icon');
    const quickIcon = document.getElementById('quick-refresh-icon');
    const badge = document.getElementById('live-count-badge');

    if (syncIcon) syncIcon.classList.add('fa-spin');
    if (cardIcon) cardIcon.classList.add('fa-spin');
    if (mobileIcon) mobileIcon.classList.add('fa-spin');
    if (quickIcon) quickIcon.classList.add('fa-spin');
    if (syncBtn) syncBtn.disabled = true;
    if (cardBtn) cardBtn.disabled = true;
    if (syncText) syncText.textContent = "Güncelleniyor...";

    showToast("🔄 Canlı bülten taranıyor ve yeni kuponlar üretiliyor...");

    try {
        currentRotation++;
        const res = await fetch('/api/refresh-coupons', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rotation: currentRotation })
        });
        const data = await res.json();
        if (data.success && data.coupons) {
            allCouponsData = data.coupons;
            if (badge && data.match_count) {
                badge.textContent = `${data.match_count} Maç`;
            }
            renderActiveCoupon();
            showToast("✓ Canlı kuponlar ve kısa analiz notları güncellendi!");
        } else {
            await loadCoupons();
            showToast("✓ Kuponlar güncellendi!");
        }
    } catch (err) {
        console.error(err);
        showToast("Kupon güncelleme sırasında bağlantı hatası oluştu.", true);
    } finally {
        if (syncIcon) syncIcon.classList.remove('fa-spin');
        if (cardIcon) cardIcon.classList.remove('fa-spin');
        if (mobileIcon) mobileIcon.classList.remove('fa-spin');
        if (quickIcon) quickIcon.classList.remove('fa-spin');
        if (syncBtn) syncBtn.disabled = false;
        if (cardBtn) cardBtn.disabled = false;
        if (syncText) syncText.textContent = "Kuponları Güncelle";
    }
}

// Nesine Canlı Bülten Senkronizasyon Butonu (Aynı yenilemeyi tetikler)
function syncNesineData() {
    return refreshAllCoupons();
}

function renderBulletin(matches) {
    const grid = document.getElementById('matches-grid');
    grid.innerHTML = '';

    if (!matches || matches.length === 0) {
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">Aramanıza uygun karşılaşma bulunamadı.</div>`;
        return;
    }

    matches.forEach(m => {
        const card = document.createElement('div');
        card.className = "bg-cardbg border border-cardborder rounded-2xl p-5 hover:border-slate-600 transition shadow-md flex flex-col justify-between";

        const dayTag = m.day === 'today' ? 
            `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold text-[10px] border border-rose-500/30">BUGÜN</span>` :
            `<span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold text-[10px] border border-blue-500/30">YARIN</span>`;

        // Last 5 scores render
        const renderLast5 = (teamName, list) => {
            if (!list || list.length === 0) return '';
            let html = `<div class="text-[11px] text-slate-400 mt-2"><strong class="text-slate-300">${teamName} Son Maçlar:</strong><div class="flex flex-wrap gap-1.5 mt-1">`;
            list.forEach(g => {
                const bttsBothPill = g.btts_both ? 
                    `<span class="text-[9px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-700/50 font-bold">1.Y/2.Y KG ✓</span>` : '';
                html += `<span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300">${g.opp} ${g.score} (İY: ${g.ht}) ${bttsBothPill}</span>`;
            });
            html += `</div></div>`;
            return html;
        };

        const homeHistory = renderLast5(m.home_team, m.home_last_5);
        const awayHistory = renderLast5(m.away_team, m.away_last_5);

        // Net pazar oranları özeti
        const oddMs1 = m.odds.ms1 ? m.odds.ms1.toFixed(2) : '-';
        const oddMs2 = m.odds.ms2 ? m.odds.ms2.toFixed(2) : '-';
        const oddOver25 = m.odds.over25 ? m.odds.over25.toFixed(2) : '-';
        const oddBtts = m.odds.btts_yes ? m.odds.btts_yes.toFixed(2) : '-';
        const oddBothHalves = m.odds.both_halves_btts_yes ? m.odds.both_halves_btts_yes.toFixed(2) : '-';
        const rec = m.recommendation || { pick: 'MS 1', odd: 1.50, prob: 65 };
        const cleanId = m.nesine_code || m.id.replace('st-', '').replace('nesine-', '');
        const matchCodeLabel = `Bülten Kodu: #${cleanId}`;

        card.innerHTML = `
            <div>
                <!-- League & Time -->
                <div class="flex items-center justify-between text-xs text-slate-400 mb-3">
                    <span class="font-bold text-slate-200 flex items-center gap-1.5 truncate max-w-[200px]">
                        <span>${m.country}</span>
                        <span>•</span>
                        <span class="truncate">${m.league}</span>
                    </span>
                    <div class="flex items-center gap-2">
                        ${dayTag}
                        <span class="text-slate-400 text-xs">${m.match_time}</span>
                    </div>
                </div>

                <!-- Teams & VS -->
                <div class="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-cardborder mb-2">
                    <span class="font-black text-white text-sm sm:text-base">${m.home_team}</span>
                    <span class="text-[10px] font-bold text-slate-400 px-2 py-0.5 rounded bg-slate-800">VS</span>
                    <span class="font-black text-white text-sm sm:text-base text-right">${m.away_team}</span>
                </div>

                <div class="text-[11px] text-slate-500 mb-2.5 flex items-center justify-between">
                    <span class="font-mono text-emerald-400 font-bold">${matchCodeLabel}</span>
                    <span class="text-emerald-300 font-bold">🛡️ AI: ${rec.pick} (${rec.odd ? rec.odd.toFixed(2) : '-'} | %${Math.round(rec.prob || 65)})</span>
                </div>

                <!-- Net Pazarlar -->
                <div class="grid grid-cols-4 gap-1.5 text-center text-xs mb-3 font-mono">
                    <div class="p-2 rounded-xl bg-slate-900/80 border border-slate-700/60">
                        <span class="text-[9px] text-slate-400 block font-sans font-bold">MS 1 / 2</span>
                        <span class="text-xs font-black text-white">${oddMs1} / ${oddMs2}</span>
                    </div>
                    <div class="p-2 rounded-xl bg-amber-950/20 border border-amber-500/30">
                        <span class="text-[9px] text-amber-300 block font-sans font-bold">2,5 Üst</span>
                        <span class="text-sm font-black text-amber-400">${oddOver25}</span>
                    </div>
                    <div class="p-2 rounded-xl bg-teal-950/20 border border-teal-500/30">
                        <span class="text-[9px] text-teal-300 block font-sans font-bold">KG Evet</span>
                        <span class="text-sm font-black text-teal-400">${oddBtts}</span>
                    </div>
                    <div class="p-2 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
                        <span class="text-[9px] text-emerald-300 block font-sans font-bold">Evet/Evet</span>
                        <span class="text-sm font-black text-emerald-400">${oddBothHalves}</span>
                    </div>
                </div>

                <!-- Deep Last 5 Matches History -->
                <div class="bg-slate-900/40 p-3 rounded-xl border border-slate-800/80">
                    <span class="text-[11px] font-bold text-slate-300 flex items-center gap-1">
                        <i class="fa-solid fa-clock-rotate-left text-slate-400"></i> Geçmiş Son 5 Maçın Devre Skorları
                    </span>
                    ${homeHistory}
                    ${awayHistory}
                </div>
            </div>
        `;

        // Derin Analiz ve Tüm Oranlar butonları - card footer
        const footer = document.createElement('div');
        footer.style.cssText = 'margin-top:12px;padding-top:10px;border-top:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;';
        const oddsCountLabel = m.odds_count ? `${m.odds_count} Oran` : 'Tüm Oranlar';
        footer.innerHTML = `
            <button onclick="openAllOddsModal('${m.id}')" class="px-2.5 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/40 text-xs font-bold transition flex items-center gap-1.5 shadow-sm" title="Nesine ve platformların tüm ${m.odds_count || 400}+ bahis çeşidini gör">
                <i class="fa-solid fa-list-ol text-indigo-400"></i> ${oddsCountLabel}
            </button>
            <button onclick="showDeepAnalysis('${m.id}')" class="btn-deep-analysis">🔬 Derin Analiz</button>
        `;
        card.appendChild(footer);

        grid.appendChild(card);
    });
}

function filterBulletin() {
    const dayVal = document.getElementById('bulletin-day-filter').value;
    const searchInput = document.getElementById('bulletin-search-input');
    const searchVal = searchInput ? searchInput.value.toLowerCase().trim() : '';

    let filtered = allMatchesData;
    if (dayVal !== 'all') {
        filtered = filtered.filter(m => m.day === dayVal);
    }
    if (searchVal) {
        filtered = filtered.filter(m => 
            m.home_team.toLowerCase().includes(searchVal) ||
            m.away_team.toLowerCase().includes(searchVal) ||
            m.league.toLowerCase().includes(searchVal) ||
            (m.country && m.country.toLowerCase().includes(searchVal)) ||
            (m.nesine_code && m.nesine_code.toString().includes(searchVal))
        );
    }
    renderBulletin(filtered);
}

// 3. Güven Odaklı Özel Kupon Sihirbazı
async function generateCustomMegaCoupon(event) {
    event.preventDefault();
    const form = event.target;
    const matchCount = form.querySelector('input[name="match_count"]:checked').value;
    const styleEl = form.querySelector('input[name="coupon_style"]:checked');
    const couponStyle = styleEl ? styleEl.value : 'net_guven';

    const resDiv = document.getElementById('wizard-result');
    resDiv.classList.remove('hidden');
    resDiv.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <i class="fa-solid fa-circle-notch fa-spin text-2xl text-emerald-500 mb-2"></i>
            <p>Ortak bülten havuzu taranıyor ve ${matchCount} maçlık yüksek güvenli kupon hazırlanıyor...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/custom-coupon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ match_count: matchCount, risk_level: couponStyle })
        });

        const data = await res.json();
        if (data.success && data.coupon) {
            const c = data.coupon;
            let matchesHtml = '';
            c.matches.forEach((m) => {
                const confBadge = m.confidence_label || `%${Math.round(m.confidence || 70)} Güven`;
                matchesHtml += `
                    <div class="p-3 bg-slate-900 rounded-xl border border-cardborder">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-bold text-white text-sm">⚽ ${m.match_name}</div>
                                <div class="text-xs text-slate-400">${m.league} • ${m.time}</div>
                            </div>
                            <div class="text-right">
                                <span class="font-mono font-black text-emerald-400 text-base">${m.odd.toFixed(2)}</span>
                                <span class="block text-[10px] text-emerald-300 font-bold">🛡️ ${confBadge}</span>
                            </div>
                        </div>
                        <div class="mt-1.5 flex items-center gap-2">
                            <span class="px-2 py-0.5 rounded bg-emerald-600/30 border border-emerald-500/40 text-emerald-200 text-xs font-bold">${m.pick}</span>
                        </div>
                        <div class="mt-1 text-[11px] text-slate-400">📝 Not: ${getShortMatchNote(m)}</div>
                    </div>
                `;
            });

            const return50 = Math.round(c.total_odd * 50).toLocaleString('tr-TR');
            const return100 = Math.round(c.total_odd * 100).toLocaleString('tr-TR');

            resDiv.innerHTML = `
                <div class="bg-gradient-to-br from-slate-900 to-emerald-950/40 border border-emerald-500/30 rounded-2xl p-5 shadow-xl">
                    <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
                        <span class="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            🛡️ Ort. Güven: %${Math.round(c.avg_confidence || 74)}
                        </span>
                        <div class="text-right font-mono">
                            <span class="text-xs text-slate-400 block">TOPLAM ORAN</span>
                            <span class="text-2xl font-black text-emerald-400">${c.total_odd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                        </div>
                    </div>
                    <p class="text-xs text-slate-300 mb-4">${c.summary}</p>
                    <div class="space-y-2 mb-4">${matchesHtml}</div>
                    <div class="p-3 rounded-xl bg-slate-900/80 border border-cardborder flex justify-between items-center text-xs flex-wrap gap-2">
                        <span class="text-slate-200">50 TL Kupon Kazancı: <strong class="text-emerald-400 font-black text-sm">${return50} TL</strong></span>
                        <span class="text-slate-400">100 TL ile: <strong class="text-slate-200">${return100} TL</strong></span>
                    </div>
                </div>
            `;
            showToast("✓ Yüksek güvenli kupon oluşturuldu!");
        } else {
            resDiv.innerHTML = `<div class="p-4 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs text-center">${data.error}</div>`;
        }
    } catch (err) {
        console.error(err);
        resDiv.innerHTML = `<div class="text-rose-400 text-xs text-center">İstek işlenirken hata oluştu.</div>`;
    }
}

// ================= PWA & ANDROID MOBİL ENTEGRASYONU =================
// 1. Service Worker Kaydı (Android PWA Standalone Desteği)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('İddaa AI ServiceWorker Aktif:', reg.scope))
            .catch(err => console.log('ServiceWorker Hatası:', err));
    });
}

// 2. Android Chrome Native "Uygulamayı Telefona Yükle" Yakalayıcısı
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.classList.remove('hidden');

    const btn = document.getElementById('pwa-install-btn');
    if (btn) {
        btn.onclick = async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log('PWA Yükleme Sonucu:', outcome);
                deferredPrompt = null;
                banner.classList.add('hidden');
                if (outcome === 'accepted') {
                    showToast('🎉 İddaa AI telefonunuza başarıyla yüklendi!');
                }
            }
        };
    }
});

// 3. Android Mobil QR & Bağlantı Modalı (Genel İnternet / Wi-Fi)
let currentMobileUrl = '';
let mobileInfoData = null;
let currentMobileMode = 'public';

function toggleMobileView(mode) {
    currentMobileMode = mode;
    const btnPublic = document.getElementById('btn-mobile-view-public');
    const btnLocal = document.getElementById('btn-mobile-view-local');
    const urlLabel = document.getElementById('mobile-url-label');
    const urlText = document.getElementById('mobile-url-text');
    const qrImg = document.getElementById('mobile-qr-img');
    const step1 = document.getElementById('mobile-step1-text');

    if (!mobileInfoData) return;

    if (mode === 'public') {
        if (btnPublic) btnPublic.className = "flex-1 py-1.5 rounded-lg bg-cyan-600 text-white shadow transition flex items-center justify-center gap-1.5";
        if (btnLocal) btnLocal.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-white transition flex items-center justify-center gap-1.5";
        
        const targetUrl = mobileInfoData.public_url || mobileInfoData.mobile_url;
        currentMobileUrl = targetUrl;
        if (urlLabel) urlLabel.textContent = "🌐 Genel HTTPS Adresi (Tüm Telefonlar & Arkadaşlar)";
        if (urlText) urlText.textContent = targetUrl;
        if (qrImg) qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=5&data=${encodeURIComponent(targetUrl)}`;
        if (step1) step1.textContent = "Arkadaşınıza yukarıdaki linki WhatsApp/Telegram ile gönderin veya QR kodu kamerayla okutun (4.5G hücresel veride dahi anında açılır).";
    } else {
        if (btnPublic) btnPublic.className = "flex-1 py-1.5 rounded-lg text-slate-400 hover:text-white transition flex items-center justify-center gap-1.5";
        if (btnLocal) btnLocal.className = "flex-1 py-1.5 rounded-lg bg-cyan-600 text-white shadow transition flex items-center justify-center gap-1.5";
        
        const targetUrl = mobileInfoData.local_url;
        currentMobileUrl = targetUrl;
        if (urlLabel) urlLabel.textContent = "🏠 Yerel Wi-Fi Adresi (Ev İçi Ağ)";
        if (urlText) urlText.textContent = targetUrl;
        if (qrImg) qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=5&data=${encodeURIComponent(targetUrl)}`;
        if (step1) step1.textContent = "Telefonunuzun bu bilgisayarla AYNI ev Wi-Fi ağına bağlı olduğundan emin olun ve tarayıcıda açın.";
    }
}

async function openMobileModal() {
    const modal = document.getElementById('mobile-modal');
    if (modal) modal.classList.remove('hidden');

    try {
        const res = await fetch('/api/mobile-info');
        const data = await res.json();
        if (data.success) {
            mobileInfoData = data;
            toggleMobileView(data.public_url ? 'public' : 'local');
        }
    } catch (err) {
        console.error('Mobil bilgi alınamadı:', err);
    }
}

function closeMobileModal() {
    const modal = document.getElementById('mobile-modal');
    if (modal) modal.classList.add('hidden');
}

function copyMobileUrl() {
    const urlText = currentMobileUrl || document.getElementById('mobile-url-text')?.textContent || window.location.href;
    navigator.clipboard.writeText(urlText).then(() => {
        showToast('📱 Telefon bağlantı adresi kopyalandı!');
    }).catch(() => {
        showToast('Adres: ' + urlText);
    });
}

// ================= CANLI ARAMA & TÜRK İDDAA + TİPİCO SİTELERİ ENTEGRASYONU =================
const PLATFORM_URLS = {
    'nesine': 'https://www.nesine.com/iddaa/futbol',
    'misli': 'https://www.misli.com/iddaa/futbol',
    'bilyoner': 'https://www.bilyoner.com/iddaa',
    'birebin': 'https://www.birebin.com/anasayfa',
    'oley': 'https://www.oley.com/iddaa',
    'iddaa': 'https://www.iddaa.com/program/futbol',
    'tipico': 'https://sports.tipico.de/tr/live/default'
};

function openSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) modal.classList.remove('hidden');
    const inp = document.getElementById('global-search-input');
    if (inp) {
        inp.focus();
        handleGlobalSearch(inp.value || '');
    }
}

function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) modal.classList.add('hidden');
}

function clearSearchInput() {
    const inp = document.getElementById('global-search-input');
    if (inp) {
        inp.value = '';
        handleGlobalSearch('');
    }
}

function searchOnExternal(platform) {
    const base = PLATFORM_URLS[platform] || 'https://www.nesine.com/iddaa/futbol';
    window.open(base, '_blank');
}

function handleGlobalSearch(query) {
    const clearBtn = document.getElementById('clear-search-btn');
    if (clearBtn) {
        if (query) clearBtn.classList.remove('hidden');
        else clearBtn.classList.add('hidden');
    }

    const container = document.getElementById('search-results-container');
    if (!container) return;

    const q = (query || '').toLowerCase().trim();

    let matched = [];
    if (!q) {
        matched = allMatchesData.slice(0, 12);
    } else {
        matched = allMatchesData.filter(m => {
            const matchName = `${m.home_team} ${m.away_team}`.toLowerCase();
            const league = (m.league || '').toLowerCase();
            const rec = (m.recommendation ? m.recommendation.pick : '').toLowerCase();
            return matchName.includes(q) || league.includes(q) || rec.includes(q);
        });
    }

    if (matched.length === 0) {
        container.innerHTML = `
            <div class="py-8 text-center text-slate-400">
                <i class="fa-solid fa-futbol text-3xl mb-2 text-slate-600 block"></i>
                <p class="font-bold text-sm text-slate-300">"${query}" ile eşleşen canlı maç bulunamadı.</p>
                <p class="text-xs text-slate-500 mt-1">Yukarıdaki butonlardan doğrudan Nesine, Misli veya Tipico'da arayabilirsiniz.</p>
            </div>
        `;
        return;
    }

    let html = '';
    matched.slice(0, 25).forEach(m => {
        const nesineCode = m.id.replace('nesine-', '');
        const rec = m.recommendation || { pick: 'Maç Sonucu 1', odd: 1.85 };
        const oddVal = rec.odd ? rec.odd.toFixed(2) : '1.90';

        html += `
            <div class="bg-slate-900/90 border border-slate-800 hover:border-amber-500/50 rounded-2xl p-3.5 transition">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
                    <div class="flex items-center space-x-2">
                        <span class="text-sm">⚽</span>
                        <strong class="text-white text-sm tracking-tight">${m.home_team} - ${m.away_team}</strong>
                    </div>
                    <div class="flex items-center gap-1.5 text-[11px] font-mono">
                        <span class="text-amber-400 font-bold px-2 py-0.5 rounded-lg bg-amber-950/60 border border-amber-600/30">Bülten Kodu: #${nesineCode}</span>
                        <span class="text-slate-400">${m.match_time}</span>
                    </div>
                </div>

                <div class="text-xs text-slate-400 mb-2 pl-5 flex items-center justify-between">
                    <span>${m.country} ${m.league}</span>
                    <span class="text-emerald-400 font-bold">Beklenen Gol (xG): ${m.expected_goals ? m.expected_goals.total_xg : '2.6'}</span>
                </div>

                <!-- AI Pick Bar -->
                <div class="bg-slate-950/80 border border-slate-800/80 rounded-xl p-2.5 px-3 flex items-center justify-between mb-2.5">
                    <div class="flex items-center space-x-2">
                        <i class="fa-solid fa-robot text-rose-400 text-xs"></i>
                        <span class="text-xs text-slate-200 font-bold">${rec.pick}</span>
                    </div>
                    <span class="text-xs font-mono font-black text-emerald-400">${oddVal} Oran</span>
                </div>

                <!-- Direct Platform Action Buttons for this Match -->
                <div class="flex items-center gap-1.5 overflow-x-auto pt-1 scrollbar-none text-[10px] font-bold">
                    <a href="https://www.nesine.com/iddaa/futbol" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-emerald-950 text-emerald-300 border border-emerald-600/30 hover:bg-emerald-900 transition flex items-center gap-1 shrink-0">
                        <span>🟢 Nesine</span>
                    </a>
                    <a href="https://www.misli.com/iddaa/futbol" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-yellow-950 text-yellow-300 border border-yellow-600/30 hover:bg-yellow-900 transition flex items-center gap-1 shrink-0">
                        <span>🟡 Misli</span>
                    </a>
                    <a href="https://www.bilyoner.com/iddaa" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-blue-950 text-blue-300 border border-blue-600/30 hover:bg-blue-900 transition flex items-center gap-1 shrink-0">
                        <span>🔵 Bilyoner</span>
                    </a>
                    <a href="https://www.birebin.com/anasayfa" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-purple-950 text-purple-300 border border-purple-600/30 hover:bg-purple-900 transition flex items-center gap-1 shrink-0">
                        <span>🟣 Birebin</span>
                    </a>
                    <a href="https://www.oley.com/iddaa" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-teal-950 text-teal-300 border border-teal-600/30 hover:bg-teal-900 transition flex items-center gap-1 shrink-0">
                        <span>🟢 Oley</span>
                    </a>
                    <a href="https://www.iddaa.com/program/futbol" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-slate-800 text-slate-200 border border-slate-600 hover:bg-slate-700 transition flex items-center gap-1 shrink-0">
                        <span>🇹🇷 İddaa</span>
                    </a>
                    <a href="https://sports.tipico.de/tr/live/default" target="_blank" rel="noopener" class="px-2 py-1 rounded-md bg-rose-950 text-rose-300 border border-rose-600/30 hover:bg-rose-900 transition flex items-center gap-1 shrink-0">
                        <span>🇩🇪 Tipico Canlı Kıyasla</span>
                    </a>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}


// ============================================================
// DERIN ANALIZ FONKSİYONLARI
// ============================================================

async function showDeepAnalysis(matchId) {
  document.getElementById('deepAnalysisModal').style.display = 'flex';
  document.getElementById('deepAnalysisContent').innerHTML = '<div class="loading-spin">🔄 Gerçek veriler çekiliyor...</div>';

  try {
    const resp = await fetch(`/api/match-deep-analysis/${matchId}`);
    const data = await resp.json();

    if (data.success) {
      renderDeepAnalysis(data.analysis, matchId);
    } else {
      document.getElementById('deepAnalysisContent').innerHTML = `<p class="error-msg">❌ ${data.error}</p>`;
    }
  } catch (e) {
    document.getElementById('deepAnalysisContent').innerHTML = `<p class="error-msg">❌ Bağlantı hatası</p>`;
  }
}

function closeDeepAnalysis() {
  document.getElementById('deepAnalysisModal').style.display = 'none';
}

function renderDeepAnalysis(analysis, matchId) {
  const hf = analysis.home_form;
  const af = analysis.away_form;
  const sq = analysis.squad_status;
  const h2h = analysis.h2h;
  const fl = analysis.fixture_load;
  const gs = analysis.goal_stats;
  const recs = analysis.recommendations || [];

  // Form gösterimi
  const formBar = (score) => {
    const pct = Math.min(100, Math.max(0, score));
    const color = pct >= 60 ? '#22c55e' : (pct >= 40 ? '#f59e0b' : '#ef4444');
    return `<div style="background:#1e293b;border-radius:8px;height:10px;overflow:hidden;margin:4px 0">
      <div style="width:${pct}%;background:${color};height:100%;border-radius:8px;transition:width 0.5s"></div>
    </div><small style="color:${color}">${pct}% form puanı</small>`;
  };

  const resultBadge = (r) => {
    const colors = {W:'#22c55e',D:'#f59e0b',L:'#ef4444','?':'#64748b'};
    return `<span style="display:inline-block;width:26px;height:26px;line-height:26px;text-align:center;border-radius:50%;background:${colors[r]||'#64748b'};color:#fff;font-size:12px;font-weight:bold;margin:1px">${r}</span>`;
  };

  const squadHTML = (squad) => {
    let html = `<div style="margin-bottom:8px"><span style="color:#f8fafc;font-weight:600">${squad.status}</span></div>`;
    if (squad.injured && squad.injured.length > 0) {
      html += `<div style="margin:4px 0"><span style="color:#ef4444">🚑 Sakat (${squad.injured.length}):</span> ${squad.injured.map(p=>p.name||p).join(', ')}</div>`;
    }
    if (squad.suspended && squad.suspended.length > 0) {
      html += `<div style="margin:4px 0"><span style="color:#f59e0b">🟨 Cezalı (${squad.suspended.length}):</span> ${squad.suspended.map(p=>p.name||p).join(', ')}</div>`;
    }
    if (squad.doubtful && squad.doubtful.length > 0) {
      html += `<div style="margin:4px 0"><span style="color:#64748b">❓ Şüpheli (${squad.doubtful.length}):</span> ${squad.doubtful.map(p=>p.name||p).join(', ')}</div>`;
    }
    if ((!squad.injured || squad.injured.length === 0) && (!squad.suspended || squad.suspended.length === 0)) {
      html += '<div style="color:#22c55e">✅ Kayda değer eksik bilgisi yok</div>';
    }
    return html;
  };

  const h2hHTML = () => {
    if (!h2h.recent || h2h.recent.length === 0) return '<small style="color:#64748b">H2H verisi bulunamadı</small>';
    return `<div style="margin-bottom:8px;color:#f8fafc;font-weight:600">${h2h.summary}</div>` +
      h2h.recent.map(r => `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1e293b;font-size:13px">
        <span style="color:#94a3b8">${r.date||''}</span>
        <span style="color:#e2e8f0">${r.home} vs ${r.away}</span>
        <span style="color:#f59e0b;font-weight:600">${r.score}</span>
      </div>`).join('');
  };

  const recsHTML = recs.map(r => `
    <div style="background:#0f172a;border-left:3px solid ${r.confidence==='Yüksek'?'#22c55e':r.confidence==='Orta-Yüksek'?'#f59e0b':'#3b82f6'};padding:10px 14px;border-radius:0 8px 8px 0;margin:6px 0">
      <div style="font-weight:600;color:#f8fafc">${r.icon} ${r.pick} <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:${r.confidence==='Yüksek'?'#166534':r.confidence==='Orta-Yüksek'?'#78350f':'#1e3a5f'};color:#fff">${r.confidence}</span></div>
      <div style="color:#94a3b8;font-size:13px;margin-top:4px">${r.reason}</div>
    </div>`).join('');

  document.getElementById('deepAnalysisContent').innerHTML = `
    <div style="font-family:'Inter',sans-serif;color:#f8fafc">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px">
        <h2 style="margin:0;font-size:20px">🔬 Derinlemesine Analiz</h2>
        <span style="font-size:12px;color:#64748b">${analysis.data_source} ${analysis.real_data_timestamp?'| '+analysis.real_data_timestamp:''}</span>
      </div>

      <!-- AI Önerileri -->
      ${recs.length > 0 ? `<div style="margin-bottom:20px">
        <h3 style="color:#f59e0b;margin:0 0 10px 0;font-size:15px">🤖 AI Analiz Önerileri</h3>
        ${recsHTML}
      </div>` : ''}

      <!-- Form Analizi -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 10px 0;color:#60a5fa;font-size:14px">🏠 Ev Sahibi Form</h4>
          <div style="font-size:22px;font-weight:800;margin-bottom:4px">${hf.form_string||'?????'}</div>
          ${formBar(hf.score)}
          <div style="color:#94a3b8;font-size:13px;margin-top:6px">${hf.trend}</div>
          <div style="margin-top:8px;font-size:12px;color:#64748b">${hf.wins}G ${hf.draws}B ${hf.losses}M (son 5)</div>
        </div>
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 10px 0;color:#f472b6;font-size:14px">✈️ Deplasman Form</h4>
          <div style="font-size:22px;font-weight:800;margin-bottom:4px">${af.form_string||'?????'}</div>
          ${formBar(af.score)}
          <div style="color:#94a3b8;font-size:13px;margin-top:6px">${af.trend}</div>
          <div style="margin-top:8px;font-size:12px;color:#64748b">${af.wins}G ${af.draws}B ${af.losses}M (son 5)</div>
        </div>
      </div>

      <!-- Gol İstatistikleri -->
      <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px">
        <h4 style="margin:0 0 12px 0;color:#a78bfa;font-size:14px">⚽ Gol İstatistikleri</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;text-align:center">
          <div><div style="font-size:24px;font-weight:800;color:#22c55e">${gs.home_scored_avg}</div><div style="color:#64748b;font-size:11px">Ev Sahibi<br>Attığı Ort.</div></div>
          <div><div style="font-size:24px;font-weight:800;color:#f59e0b">${gs.total_avg}</div><div style="color:#64748b;font-size:11px">Toplam<br>Gol Beklentisi</div></div>
          <div><div style="font-size:24px;font-weight:800;color:#22c55e">${gs.away_scored_avg}</div><div style="color:#64748b;font-size:11px">Deplasman<br>Attığı Ort.</div></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;text-align:center;margin-top:12px;padding-top:12px;border-top:1px solid #0f172a">
          <div><div style="font-size:18px;font-weight:700;color:#ef4444">${gs.home_conceded_avg}</div><div style="color:#64748b;font-size:11px">Ev Sahibi Yediği Ort.</div></div>
          <div><div style="font-size:18px;font-weight:700;color:#ef4444">${gs.away_conceded_avg}</div><div style="color:#64748b;font-size:11px">Deplasman Yediği Ort.</div></div>
        </div>
      </div>

      <!-- İY / MS Skor Dağılımı (Devre ve Maç Skoru) -->
      ${analysis.iyms_scores ? `
      <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid #3b82f640">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
          <h4 style="margin:0;color:#38bdf8;font-size:14px">⏱️ İY / MS Skor Tahminleri (Devre & Maç Skoru)</h4>
          <span style="background:#38bdf820;color:#38bdf8;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:bold;border:1px solid #38bdf850">🎯 En Olası: ${analysis.iyms_scores.display}</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
          <div>
            <div style="color:#94a3b8;font-size:11px;font-weight:bold;margin-bottom:6px">⚡ 1. YARI (DEVRE) SKORLARI</div>
            ${analysis.iyms_scores.top_ht.map(item => `
              <div style="display:flex;justify-content:space-between;padding:5px 8px;background:#0f172a;border-radius:6px;margin-bottom:4px;font-size:12px">
                <span style="color:#e2e8f0;font-weight:bold">İlk Yarı ${item.score}</span>
                <span style="color:#38bdf8;font-weight:bold">%${item.prob}</span>
              </div>
            `).join('')}
          </div>
          <div>
            <div style="color:#94a3b8;font-size:11px;font-weight:bold;margin-bottom:6px">🏁 90 DAKİKA MAÇ SKORLARI</div>
            ${analysis.iyms_scores.top_ft.map(item => `
              <div style="display:flex;justify-content:space-between;padding:5px 8px;background:#0f172a;border-radius:6px;margin-bottom:4px;font-size:12px">
                <span style="color:#e2e8f0;font-weight:bold">Maç Sonu ${item.score}</span>
                <span style="color:#4ade80;font-weight:bold">%${item.prob}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
      ` : ''}

      <!-- Kadro Durumu -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 10px 0;color:#fb923c;font-size:14px">🏥 Ev Sahibi Kadro</h4>
          ${squadHTML(sq.home)}
        </div>
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 10px 0;color:#fb923c;font-size:14px">🏥 Deplasman Kadro</h4>
          ${squadHTML(sq.away)}
        </div>
      </div>

      <!-- H2H -->
      <div style="background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px">
        <h4 style="margin:0 0 12px 0;color:#34d399;font-size:14px">⚔️ Tarihsel Karşılaşmalar (H2H)</h4>
        ${h2hHTML()}
      </div>

      <!-- Fikstür Yoğunluğu -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 8px 0;color:#94a3b8;font-size:14px">📅 Ev Sahibi Fikstür</h4>
          <div style="margin-bottom:8px">${fl.home.fatigue_risk}</div>
          ${fl.home.has_european ? '<div style="color:#f59e0b;font-size:12px">🌍 Avrupa maçı var!</div>' : ''}
          ${fl.home.upcoming && fl.home.upcoming.length > 0 ? fl.home.upcoming.map(e=>`<div style="color:#64748b;font-size:12px">📌 ${e.date||''} - ${e.opponent||''} (${e.competition||''})</div>`).join('') : '<div style="color:#64748b;font-size:12px">Yaklaşan maç bilgisi yok</div>'}
        </div>
        <div style="background:#1e293b;border-radius:12px;padding:16px">
          <h4 style="margin:0 0 8px 0;color:#94a3b8;font-size:14px">📅 Deplasman Fikstür</h4>
          <div style="margin-bottom:8px">${fl.away.fatigue_risk}</div>
          ${fl.away.has_european ? '<div style="color:#f59e0b;font-size:12px">🌍 Avrupa maçı var!</div>' : ''}
          ${fl.away.upcoming && fl.away.upcoming.length > 0 ? fl.away.upcoming.map(e=>`<div style="color:#64748b;font-size:12px">📌 ${e.date||''} - ${e.opponent||''} (${e.competition||''})</div>`).join('') : '<div style="color:#64748b;font-size:12px">Yaklaşan maç bilgisi yok</div>'}
        </div>
      </div>
    </div>
  `;
}

// ==============================================================================
// TÜM ORANLAR & BAHİS ÇEŞİTLERİ MODAL SİSTEMİ (400-500+ Oran Havuzu)
// ==============================================================================
let currentAllOddsData = null;
let currentAllOddsCategory = 'all';
let currentAllOddsSearch = '';

async function openAllOddsModal(matchId) {
    const modal = document.getElementById('allOddsModal');
    const content = document.getElementById('allOddsModalContent');
    if (!modal || !content) return;

    modal.style.display = 'flex';
    content.innerHTML = `
        <div class="py-16 text-center text-slate-300">
            <i class="fa-solid fa-spinner fa-spin text-3xl text-indigo-400 mb-3 block"></i>
            <p class="font-bold text-base">Bültendeki tüm 90+ piyasa ve 400-500+ oran seçeneği yükleniyor...</p>
            <span class="text-xs text-slate-500">Nesine ve tüm platformların eşit havuzu işleniyor</span>
        </div>
    `;

    try {
        const res = await fetch(`/api/match-all-odds/${matchId}`);
        const data = await res.json();
        if (!data.success) {
            content.innerHTML = `<div class="p-8 text-center text-rose-400 font-bold">Oran verisi alınamadı: ${data.error || 'Bilinmeyen hata'}</div>`;
            return;
        }
        currentAllOddsData = data;
        currentAllOddsCategory = 'all';
        currentAllOddsSearch = '';
        renderAllOddsModal();
    } catch (err) {
        content.innerHTML = `<div class="p-8 text-center text-rose-400 font-bold">Bağlantı hatası: ${err.message}</div>`;
    }
}

function closeAllOddsModal() {
    const modal = document.getElementById('allOddsModal');
    if (modal) modal.style.display = 'none';
}

function filterAllOddsCategory(category) {
    currentAllOddsCategory = category;
    renderAllOddsMarketsOnly();
}

function searchAllOdds(val) {
    currentAllOddsSearch = (val || '').toLowerCase().trim();
    renderAllOddsMarketsOnly();
}

function renderAllOddsModal() {
    const content = document.getElementById('allOddsModalContent');
    if (!content || !currentAllOddsData) return;

    const d = currentAllOddsData;
    const catKeys = Object.keys(d.categories || {});

    // Kategori butonları
    let catBtnsHtml = `
        <button onclick="filterAllOddsCategory('all')" id="allodds-tab-all" class="px-3 py-1.5 rounded-xl text-xs font-bold transition ${currentAllOddsCategory==='all' ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-800 text-slate-300 hover:text-white'}">
            Tümü (${d.odds_count})
        </button>
    `;
    catKeys.forEach(k => {
        const count = (d.categories[k] || []).reduce((acc, m) => acc + (m.outcomes || []).length, 0);
        const active = currentAllOddsCategory === k;
        catBtnsHtml += `
            <button onclick="filterAllOddsCategory('${k}')" id="allodds-tab-${k}" class="px-3 py-1.5 rounded-xl text-xs font-bold transition ${active ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-800 text-slate-300 hover:text-white'}">
                ${k} (${count})
            </button>
        `;
    });

    content.innerHTML = `
        <div class="font-sans text-slate-100">
            <!-- Header -->
            <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-4 flex-wrap gap-2">
                <div>
                    <div class="flex items-center gap-2 flex-wrap">
                        <h2 class="text-lg sm:text-xl font-black text-white">⚽ ${d.match_name}</h2>
                        <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold">
                            🔥 ${d.odds_count} Bahis Oranı (${d.market_count} Piyasa)
                        </span>
                    </div>
                    <div class="text-xs text-slate-400 mt-1 flex items-center gap-2">
                        <span>${d.league}</span>
                        <span>•</span>
                        <span>${d.time}</span>
                        <span>•</span>
                        <span class="text-amber-400 font-mono font-bold">Bülten #${d.bulten_code}</span>
                    </div>
                </div>
            </div>

            <!-- Arama & Filtre Çubuğu -->
            <div class="mb-4 flex items-center gap-2 flex-wrap">
                <div class="relative flex-1 min-w-[220px]">
                    <i class="fa-solid fa-search absolute left-3 top-3 text-slate-400 text-sm"></i>
                    <input type="text" oninput="searchAllOdds(this.value)" placeholder="Bahis veya oyuncu ara (Örn: Haaland, 2.5, Korner, İY...)" class="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition">
                </div>
            </div>

            <!-- Kategori Çubuğu -->
            <div class="flex items-center gap-1.5 overflow-x-auto pb-3 mb-4 scrollbar-thin">
                ${catBtnsHtml}
            </div>

            <!-- Piyasa Kartları Konteyneri -->
            <div id="allOddsMarketsContainer" class="space-y-4">
                <!-- renderAllOddsMarketsOnly ile doldurulacak -->
            </div>
        </div>
    `;

    renderAllOddsMarketsOnly();
}

function renderAllOddsMarketsOnly() {
    const container = document.getElementById('allOddsMarketsContainer');
    if (!container || !currentAllOddsData) return;

    const d = currentAllOddsData;
    let marketsToRender = [];

    if (currentAllOddsCategory === 'all') {
        marketsToRender = d.markets || [];
    } else {
        marketsToRender = (d.categories && d.categories[currentAllOddsCategory]) || [];
    }

    // Arama filtresi
    if (currentAllOddsSearch) {
        marketsToRender = marketsToRender.filter(m => {
            const titleMatch = (m.title || '').toLowerCase().includes(currentAllOddsSearch);
            const catMatch = (m.category || '').toLowerCase().includes(currentAllOddsSearch);
            const outcomeMatch = (m.outcomes || []).some(o => (o.label || '').toLowerCase().includes(currentAllOddsSearch));
            return titleMatch || catMatch || outcomeMatch;
        });
    }

    if (marketsToRender.length === 0) {
        container.innerHTML = `
            <div class="py-12 text-center text-slate-400">
                <i class="fa-solid fa-filter-circle-xmark text-2xl text-slate-500 mb-2 block"></i>
                Seçilen kategori veya arama kriterine uygun bahis bulunamadı.
            </div>
        `;
        return;
    }

    let html = '';
    marketsToRender.forEach(m => {
        // Outcome grid kolon sayısı
        const oCount = (m.outcomes || []).length;
        let gridCols = "grid-cols-2 sm:grid-cols-3";
        if (oCount === 2) gridCols = "grid-cols-2";
        else if (oCount === 3) gridCols = "grid-cols-3";
        else if (oCount >= 8) gridCols = "grid-cols-2 sm:grid-cols-3 md:grid-cols-4";

        let outcomesHtml = '';
        (m.outcomes || []).forEach(o => {
            outcomesHtml += `
                <div class="bg-slate-900/90 border border-slate-700/60 hover:border-indigo-500/60 p-2.5 rounded-xl flex items-center justify-between gap-2 transition cursor-pointer group">
                    <span class="text-xs font-bold text-slate-200 group-hover:text-white truncate">${o.label}</span>
                    <span class="font-mono font-black text-amber-400 text-sm shrink-0 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800">${Number(o.odd).toFixed(2)}</span>
                </div>
            `;
        });

        html += `
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-sm">
                <div class="flex items-center justify-between mb-2.5 pb-2 border-b border-slate-800/60 flex-wrap gap-2">
                    <div class="flex items-center gap-2">
                        <span class="font-black text-sm text-white">${m.title}</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-700/40">${m.category}</span>
                    </div>
                    <span class="text-[10px] text-slate-500 font-mono font-bold">MBS ${m.mbs || 1} • ${oCount} Seçenek</span>
                </div>
                <div class="grid ${gridCols} gap-2">
                    ${outcomesHtml}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}
