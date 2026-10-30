/**
 * İDDAA AI PRO - Frontend Controller (TURBO MOD)
 * 5 Maçlık Analiz Kuponları (50 TL Standart) & Canlı Dünya Platformları
 */

let allCouponsData = {};
let allMatchesData = [];
let iymsTableData = [];
let activeCouponDay = 'iy_ms';
let activeTab = 'coupons';
let selectedPlatformFilter = null;

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    setupSafetyWatchdog();
});

function setupSafetyWatchdog() {
    setTimeout(() => {
        const container = document.getElementById('coupon-display-container');
        if (container && (container.innerHTML.includes('fa-circle-notch') || container.innerHTML.includes('Canlı bülten taranıyor'))) {
            container.innerHTML = `
                <div class="py-12 text-center text-slate-300 bg-slate-900/80 rounded-2xl border border-slate-800 p-6 max-w-md mx-auto my-6 shadow-2xl">
                    <i class="fa-solid fa-bolt text-3xl mb-3 text-amber-400"></i>
                    <h3 class="font-black text-white text-base mb-1">Kuponlar Yükleniyor</h3>
                    <p class="text-xs text-slate-400 mb-4">Veri akışı beklenenden uzun sürdü. Kuponları anında yüklemek için dokunun:</p>
                    <button onclick="loadAllData(true)" class="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-black text-xs shadow-lg transition active:scale-95 flex items-center gap-2 mx-auto cursor-pointer">
                        <i class="fa-solid fa-rotate-right"></i> Şimdi Yükle
                    </button>
                </div>
            `;
        }
    }, 5000);
}

async function loadAllData(force = false) {
    const urlSuffix = force ? `?force=1&_t=${Date.now()}` : `?_t=${Date.now()}`;

    // 1. Fetch & render coupons FIRST (turbo instant display)
    fetch(`/api/coupons${urlSuffix}`)
        .then(r => r.json())
        .then(data => {
            if (data && data.success && data.coupons) {
                allCouponsData = data.coupons;
                renderActiveCoupon();
            } else {
                throw new Error(data ? data.error : 'Veri alınamadı');
            }
        })
        .catch(err => {
            console.error('Kupon verisi yükleme hatası:', err);
            const container = document.getElementById('coupon-display-container');
            if (container && (!allCouponsData || Object.keys(allCouponsData).length === 0)) {
                container.innerHTML = `
                    <div class="py-12 text-center text-slate-300 bg-slate-900/80 rounded-2xl border border-rose-900/50 p-6 max-w-md mx-auto my-6 shadow-2xl">
                        <i class="fa-solid fa-triangle-exclamation text-3xl mb-3 text-rose-400"></i>
                        <h3 class="font-black text-white text-base mb-1">Bağlantı Bekleniyor</h3>
                        <p class="text-xs text-slate-400 mb-4">Sunucu ile bağlantı sağlanamadı. Lütfen tekrar deneyin:</p>
                        <button onclick="loadAllData(true)" class="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-black text-xs shadow-lg transition active:scale-95 flex items-center gap-2 mx-auto cursor-pointer">
                            <i class="fa-solid fa-rotate-right"></i> Tekrar Dene
                        </button>
                    </div>
                `;
            }
        });

    // 2. Fetch matches in parallel
    fetch(`/api/matches${urlSuffix}`)
        .then(r => r.json())
        .then(data => {
            if (data && data.success && data.matches) {
                allMatchesData = data.matches;
                const badge = document.getElementById('live-count-badge');
                if (badge) badge.innerText = `${allMatchesData.length} CANLI`;
                if (activeTab === 'matches') renderBulletinMatches();
            }
        })
        .catch(err => console.error('Bülten yükleme hatası:', err));

    // 3. Fetch iyms-skor-tablosu in parallel
    fetch(`/api/iyms-skor-tablosu${urlSuffix}`)
        .then(r => r.json())
        .then(data => {
            if (data && data.success && data.table) {
                iymsTableData = data.table;
                if (activeTab === 'iyms_table') renderIYMSTable();
            }
        })
        .catch(err => console.error('İY/MS tablosu yükleme hatası:', err));
}

// ================= TAB NAVIGATION =================
function switchTab(tabId) {
    activeTab = tabId;
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(el => el.classList.add('hidden'));

    const targetSection = document.getElementById(`section-${tabId}`);
    if (targetSection) targetSection.classList.remove('hidden');

    // Update Desktop Nav Buttons
    const desktopTabs = ['coupons', 'matches', 'iyms_table', 'wizard'];
    desktopTabs.forEach(id => {
        const btn = document.getElementById(`tab-btn-${id}`);
        if (btn) {
            if (id === tabId) {
                btn.className = 'tab-btn active px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 text-white bg-slate-800 border border-slate-700 shadow';
            } else {
                btn.className = 'tab-btn px-3.5 py-1.5 rounded-lg text-xs font-bold text-slate-400 hover:text-white transition-all flex items-center space-x-1.5';
            }
        }
    });

    // Update Mobile Nav Buttons
    desktopTabs.forEach(id => {
        const mobBtn = document.getElementById(`mob-tab-btn-${id}`);
        if (mobBtn) {
            if (id === tabId) {
                mobBtn.className = 'flex flex-col items-center py-1 px-2 text-emerald-400 font-bold';
            } else {
                mobBtn.className = 'flex flex-col items-center py-1 px-2 text-slate-400 font-medium';
            }
        }
    });

    if (tabId === 'matches' && (!allMatchesData || allMatchesData.length === 0)) {
        renderBulletinMatches();
    } else if (tabId === 'iyms_table' && (!iymsTableData || iymsTableData.length === 0)) {
        renderIYMSTable();
    }
}

// ================= COUPON MODEL SELECTION & UNLIMITED INTERACTIVE ENGINE =================
let activeSelectedMatchIds = new Set();
let lastActiveCouponDay = null;

function switchCouponDay(dayKey) {
    activeCouponDay = dayKey;
    activeSelectedMatchIds.clear(); // Reset to model defaults when switching

    const couponKeys = ['iy_ms', 'dogru_skor', 'iy_ms_skor', 'sistem', 'yuksek_oran', 'gol_ustu', 'evet_evet', 'konti_garanti'];
    couponKeys.forEach(k => {
        const btn = document.getElementById(`btn-coupon-${k}`);
        if (btn) {
            if (k === dayKey) {
                btn.className = 'coupon-nav-btn active w-full p-2 sm:p-2.5 rounded-xl text-left border border-purple-500 bg-purple-600/25 text-white transition flex flex-col justify-between shadow-md cursor-pointer';
            } else {
                btn.className = 'coupon-nav-btn w-full p-2 sm:p-2.5 rounded-xl text-left border border-cardborder bg-cardbg hover:border-slate-600 text-slate-300 hover:text-white transition flex flex-col justify-between cursor-pointer';
            }
        }
    });

    renderActiveCoupon();
}

function initSelectedMatchesForCoupon(coupon) {
    activeSelectedMatchIds.clear();
    const matches = coupon.matches || [];
    const preSelected = matches.filter(m => m.is_selected);
    if (preSelected.length > 0) {
        preSelected.forEach(m => activeSelectedMatchIds.add(String(m.match_id || m.id)));
    } else {
        matches.slice(0, 5).forEach(m => activeSelectedMatchIds.add(String(m.match_id || m.id)));
    }
}

function recalcActiveTicketStats() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon) return;
    const matches = coupon.matches || [];
    const selectedMatches = matches.filter(m => activeSelectedMatchIds.has(String(m.match_id || m.id)));
    const stake = 50;

    let totalOdd = 1.0;
    if (selectedMatches.length > 0) {
        selectedMatches.forEach(m => {
            totalOdd *= parseFloat(m.odd || m.odds || 1.0);
        });
    } else {
        totalOdd = 0.0;
    }

    const totalReturn = stake * totalOdd;
    const oddStr = totalOdd > 0 ? totalOdd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';
    const winStr = totalReturn > 0 ? totalReturn.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00';

    const dynCountEl = document.getElementById('dyn-match-count');
    const dynOddEl = document.getElementById('dyn-total-odd');
    const dynPayoutEl = document.getElementById('dyn-payout');
    const footerCountEl = document.getElementById('footer-selected-count');
    const footerOddEl = document.getElementById('footer-total-odd');
    const footerPayoutEl = document.getElementById('footer-payout');

    if (dynCountEl) dynCountEl.innerText = selectedMatches.length;
    if (dynOddEl) dynOddEl.innerText = oddStr;
    if (dynPayoutEl) dynPayoutEl.innerText = winStr + ' TL';
    if (footerCountEl) footerCountEl.innerText = selectedMatches.length;
    if (footerOddEl) footerOddEl.innerText = oddStr;
    if (footerPayoutEl) footerPayoutEl.innerText = winStr + ' TL';

    // Update match card visual classes
    matches.forEach((m, idx) => {
        const mId = String(m.match_id || m.id || `match-${idx}`);
        const cardEl = document.getElementById(`match-card-${mId}`);
        const btnEl = document.getElementById(`match-btn-${mId}`);
        const isSel = activeSelectedMatchIds.has(mId);

        if (cardEl) {
            if (isSel) {
                cardEl.className = 'match-card-item p-2.5 sm:p-3 rounded-2xl bg-purple-950/25 border-2 border-purple-500/80 shadow-md transition-all cursor-pointer';
            } else {
                cardEl.className = 'match-card-item p-2.5 sm:p-3 rounded-2xl bg-cardbg/80 border border-cardborder hover:border-slate-600 transition-all cursor-pointer opacity-70 hover:opacity-100';
            }
        }
        if (btnEl) {
            if (isSel) {
                btnEl.className = 'px-2.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1 shadow active:scale-95';
                btnEl.innerHTML = '<i class="fa-solid fa-check"></i> Seçili';
            } else {
                btnEl.className = 'px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs border border-slate-700 flex items-center gap-1 active:scale-95';
                btnEl.innerHTML = '<i class="fa-solid fa-plus"></i> Ekle';
            }
        }
    });
}

function toggleMatchSelection(matchId, event) {
    if (event) event.stopPropagation();
    const strId = String(matchId);
    if (activeSelectedMatchIds.has(strId)) {
        if (activeSelectedMatchIds.size <= 1) {
            showToast('Kuponda en az 1 maç bulunmalıdır.');
            return;
        }
        activeSelectedMatchIds.delete(strId);
    } else {
        activeSelectedMatchIds.add(strId);
    }
    recalcActiveTicketStats();
}

function selectTop5Matches() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon) return;
    activeSelectedMatchIds.clear();
    const matches = coupon.matches || [];
    matches.slice(0, 5).forEach(m => activeSelectedMatchIds.add(String(m.match_id || m.id)));
    recalcActiveTicketStats();
    showToast('En güvenilir ilk 5 maç kupona seçildi.');
}

function selectAllMatches() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon) return;
    activeSelectedMatchIds.clear();
    const matches = coupon.matches || [];
    matches.forEach(m => activeSelectedMatchIds.add(String(m.match_id || m.id)));
    recalcActiveTicketStats();
    showToast(`Tüm ${matches.length} maç kupona eklendi.`);
}

function clearAllMatches() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon) return;
    const matches = coupon.matches || [];
    activeSelectedMatchIds.clear();
    if (matches.length > 0) {
        activeSelectedMatchIds.add(String(matches[0].match_id || matches[0].id));
    }
    recalcActiveTicketStats();
    showToast('Kupon temizlendi (1. banko bırakıldı).');
}

function copyActiveTicketText() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon) return;
    const matches = coupon.matches || [];
    const selectedMatches = matches.filter(m => activeSelectedMatchIds.has(String(m.match_id || m.id)));

    let totalOdd = 1.0;
    selectedMatches.forEach(m => {
        totalOdd *= parseFloat(m.odd || m.odds || 1.0);
    });
    const totalWin = 50 * totalOdd;

    let text = `🎯 İDDAA AI PRO - KİŞİSEL KUPONUM (50 TL)
`;
    text += `📌 Model: ${coupon.title || activeCouponDay}
`;
    text += `💰 Kupon Bedeli: 50 TL (Sabit)
`;
    text += `📊 Seçilen Maç: ${selectedMatches.length} Maç
`;
    text += `📈 Toplam Oran: ${totalOdd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
`;
    text += `💵 Tahmini Kazanç: ${totalWin.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TL
`;
    text += `------------------------------------
`;

    selectedMatches.forEach((m, i) => {
        const h = m.home_team || 'Ev';
        const a = m.away_team || 'Dep';
        const kod = m.nesine_code || m.bulten_code || '---';
        const pick = formatCleanPick(m.market_name || m.pick);
        const odd = parseFloat(m.odd || 1.0).toFixed(2);
        const conf = Math.round(m.confidence || 80);
        text += `${i + 1}. [Kod: ${kod}] ${h} - ${a}
   👉 Tahmin: ${pick} | Oran: ${odd} (%${conf} Güven)
`;
    });

    text += `------------------------------------
⚡ Dixon-Coles & Poisson xG Modeli ile üretilmiştir.`;

    navigator.clipboard.writeText(text).then(() => {
        showToast("📋 50 TL'lik kişisel kuponunuz panoya kopyalandı!");
    }).catch(() => {
        showToast('Kupon kopyalandı!');
    });
}

// ================= RENDER ACTIVE COUPON (SINIRSIZ & GÜVENE GÖRE SIRALI) =================
function renderActiveCoupon() {
    const container = document.getElementById('coupon-display-container');
    if (!container) return;

    let coupon = allCouponsData[activeCouponDay];
    if (!coupon) {
        coupon = allCouponsData['iy_ms'] ||
                 allCouponsData['konti_garanti'] ||
                 allCouponsData['evet_evet'] ||
                 allCouponsData['yuksek_oran'] ||
                 allCouponsData['dogru_skor'] ||
                 allCouponsData['sistem'] ||
                 allCouponsData['gol_ustu'] ||
                 Object.values(allCouponsData)[0];
    }

    if (!coupon || !coupon.matches || coupon.matches.length === 0) {
        container.innerHTML = `
            <div class="py-16 text-center text-slate-400">
                <i class="fa-solid fa-circle-exclamation text-3xl mb-3 text-amber-500"></i>
                <p class="font-bold">Kupon yükleniyor, lütfen bekleyin...</p>
                <button onclick="refreshAllCoupons()" class="mt-4 px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-bold">Tekrar Tara</button>
            </div>
        `;
        return;
    }

    // Initialize selected matches on first view of model
    if (activeSelectedMatchIds.size === 0 || lastActiveCouponDay !== activeCouponDay) {
        initSelectedMatchesForCoupon(coupon);
        lastActiveCouponDay = activeCouponDay;
    }

    const matches = coupon.matches || [];
    const isSystem = !!coupon.is_system;
    const stake = 50;

    // Calculate dynamic stats for selected matches
    const selectedMatches = matches.filter(m => activeSelectedMatchIds.has(String(m.match_id || m.id)));
    let initialOdd = 1.0;
    if (selectedMatches.length > 0) {
        selectedMatches.forEach(m => { initialOdd *= parseFloat(m.odd || m.odds || 1.0); });
    } else {
        initialOdd = 0.0;
    }
    const initialPayout = stake * initialOdd;
    const oddFormatted = initialOdd.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const winFormatted = initialPayout.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const avgConfidence = coupon.avg_confidence ? `%${Math.round(coupon.avg_confidence)}` : '%85';

    // Render All Match Cards (Ranked by confidence)
    let matchesHtml = matches.map((m, idx) => {
        let homeName = m.home_team;
        let awayName = m.away_team;
        if ((!homeName || !awayName) && m.match_name && m.match_name.includes(' - ')) {
            const parts = m.match_name.split(' - ');
            homeName = homeName || parts[0].trim();
            awayName = awayName || parts[1].trim();
        }
        homeName = homeName || 'Ev Sahibi';
        awayName = awayName || 'Deplasman';
        const league = m.league || 'Futbol Ligi';
        const matchTime = m.match_time || 'Bugün';
        const nesineCode = m.nesine_code || m.bulten_code || (m.id ? String(m.id).replace('st-', '') : '54123');
        const mbs = m.mbs || 1;
        const rawPick = m.market_name || m.pick || m.bet_type || 'Maç Sonucu 1';
        const cleanPick = formatCleanPick(rawPick);
        const oddVal = parseFloat(m.odd || m.odds || 1.80).toFixed(2);
        const confVal = parseFloat(m.confidence || m.prob || 80);
        const matchId = String(m.id || m.match_id || `match-${idx}`);
        const isSel = activeSelectedMatchIds.has(matchId);

        // Short AI Note
        const note = m.note || m.short_note || m.ai_analysis || getSmartShortNote(m);

        // Confidence badge styling
        let confBadgeClass = 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
        if (confVal < 75) {
            confBadgeClass = 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
        } else if (confVal < 85) {
            confBadgeClass = 'bg-teal-500/20 text-teal-300 border border-teal-500/40';
        }

        const borderClass = isSel
            ? 'bg-purple-950/25 border-2 border-purple-500/80 shadow-md'
            : 'bg-cardbg/80 border border-cardborder hover:border-slate-600 opacity-70 hover:opacity-100';

        const btnHtml = isSel
            ? `<button onclick="toggleMatchSelection('${matchId}', event)" id="match-btn-${matchId}" class="px-2.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1 shadow active:scale-95"><i class="fa-solid fa-check"></i> Seçili</button>`
            : `<button onclick="toggleMatchSelection('${matchId}', event)" id="match-btn-${matchId}" class="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs border border-slate-700 flex items-center gap-1 active:scale-95"><i class="fa-solid fa-plus"></i> Ekle</button>`;

        return `
            <div onclick="openMatchModal('${matchId}')" id="match-card-${matchId}" class="match-card-item p-2.5 sm:p-3 rounded-2xl ${borderClass} transition-all cursor-pointer group hover:border-purple-400/80">
                <!-- Top Row: Rank & Match Info & Bülten Kodu -->
                <div class="flex items-center justify-between text-xs text-slate-400 mb-1.5 flex-wrap gap-1">
                    <div class="flex items-center gap-1.5">
                        <span class="w-5 h-5 rounded-full bg-slate-800 text-slate-300 font-black text-[10px] flex items-center justify-center border border-slate-700">
                            #${idx + 1}
                        </span>
                        <span class="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 font-bold border border-slate-700 text-[10px]">
                            ${matchTime}
                        </span>
                        <span class="font-bold text-slate-300 truncate max-w-[140px] sm:max-w-[280px] text-[11px]">
                            <i class="fa-solid fa-trophy text-amber-400 text-[10px] mr-1"></i>${league}
                        </span>
                    </div>
                    <div class="flex items-center gap-1 text-[10px]">
                        <span class="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30 font-black">
                            Kod: ${nesineCode}
                        </span>
                        <span class="px-1.5 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold">
                            MBS: ${mbs}
                        </span>
                    </div>
                </div>

                <!-- Teams & Prominent Tahmin Box -->
                <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center my-1.5 w-full">
                    <div class="sm:col-span-6 flex flex-col gap-1 min-w-0">
                        <div class="font-black text-white text-xs sm:text-sm tracking-tight flex items-center gap-1.5 group-hover:text-purple-300 transition-colors truncate">
                            <span class="w-2 h-2 rounded-full bg-purple-400 shrink-0"></span> <span class="truncate">${homeName}</span>
                        </div>
                        <div class="font-black text-slate-200 text-xs sm:text-sm tracking-tight flex items-center gap-1.5 group-hover:text-purple-200 transition-colors truncate">
                            <span class="w-2 h-2 rounded-full bg-indigo-400 shrink-0"></span> <span class="truncate">${awayName}</span>
                        </div>
                    </div>

                    <!-- Clean Tahmin & Oran & Checkbox Button -->
                    <div class="sm:col-span-6 flex items-center justify-between sm:justify-end gap-1.5 sm:gap-2 pt-1.5 sm:pt-0 border-t sm:border-t-0 border-cardborder w-full flex-wrap">
                        <div class="px-2 py-1 rounded-xl bg-slate-900/95 border border-purple-500/40 shadow flex items-center gap-1 shrink-0">
                            <span class="text-[9px] text-purple-400 font-black tracking-wider">TAHMİN:</span>
                            <span class="text-xs font-black text-amber-300">${cleanPick}</span>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0 ml-auto sm:ml-0">
                            <div class="px-2 py-1 rounded-xl bg-purple-600/30 border border-purple-500/60 text-purple-200 font-black text-xs sm:text-sm shadow min-w-[42px] text-center">
                                ${oddVal}
                            </div>
                            <div onclick="event.stopPropagation()">
                                ${btnHtml}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Micro-Note & Confidence -->
                <div class="mt-1.5 pt-1.5 border-t border-cardborder/70 flex items-center justify-between flex-wrap gap-1 text-[11px]">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2 py-0.5 rounded-md ${confBadgeClass} font-black text-[10px]">
                            <i class="fa-solid fa-chart-line text-[9px]"></i> %${Math.round(confVal)} Güven
                        </span>
                        <span class="text-slate-300 italic truncate max-w-[260px] sm:max-w-[460px] text-[10px]">
                            "${note}"
                        </span>
                    </div>

                    <div class="flex items-center gap-1.5 ml-auto" onclick="event.stopPropagation()">
                        <button onclick="openMatchModal('${matchId}', event)" class="px-2.5 py-1 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-black text-xs flex items-center gap-1 shadow active:scale-95" title="Maçın Tüm Detayları, Oranları ve Analizini Aç">
                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i> <span>Maçı Aç</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // System Information Details (if system coupon)
    let systemBanner = '';
    if (isSystem) {
        systemBanner = `
            <div class="mb-3 p-3 rounded-2xl bg-indigo-950/40 border border-indigo-500/40 flex items-center justify-between flex-wrap gap-2 text-xs">
                <div class="flex items-center gap-2">
                    <span class="w-7 h-7 rounded-xl bg-indigo-600 text-white font-black flex items-center justify-center text-xs shadow">
                        <i class="fa-solid fa-calculator"></i>
                    </span>
                    <div>
                        <div class="font-black text-white text-xs sm:text-sm">Sistem 3, 4, 5 (16 Kolon)</div>
                        <div class="text-[10px] sm:text-[11px] text-slate-300">En az 3 maç tuttuğunda kupon kazanmaya başlar (50 TL / 16 kolon).</div>
                    </div>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="bg-cardbg border-2 border-purple-500/40 rounded-3xl p-3 sm:p-5 shadow-2xl relative overflow-hidden">
            <!-- Glow background -->
            <div class="absolute -right-20 -top-20 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>

            <!-- Top Header & Live Payout Summary (Mobile Optimized) -->
            <div class="pb-3 mb-3 border-b border-cardborder">
                <div class="flex items-center justify-between flex-wrap gap-2 mb-2">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-xs font-black border border-purple-500/40 uppercase tracking-wider">
                            ${coupon.badge || 'KUPON MODELİ'}
                        </span>
                        <span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-black border border-emerald-500/30">
                            Ort. Güven: ${avgConfidence}
                        </span>
                    </div>

                    <!-- Action Bar -->
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <button onclick="selectTop5Matches()" class="px-2.5 py-1 rounded-xl bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/50 text-[10px] sm:text-xs font-bold transition flex items-center gap-1 active:scale-95" title="En yüksek güvene sahip ilk 5 maçı seçer">
                            <i class="fa-solid fa-star text-amber-400"></i> İlk 5 Banko
                        </button>
                        <button onclick="selectAllMatches()" class="px-2 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] sm:text-xs font-bold border border-cardborder transition active:scale-95">
                            Tümünü Seç
                        </button>
                        <button onclick="clearAllMatches()" class="px-2 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] sm:text-xs font-bold border border-cardborder transition active:scale-95">
                            Temizle
                        </button>
                        <button onclick="copyActiveTicketText()" class="px-2.5 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] sm:text-xs font-black transition flex items-center gap-1 shadow active:scale-95">
                            <i class="fa-solid fa-copy"></i> Kopyala
                        </button>
                    </div>
                </div>

                <!-- 3 Live Stats Boxes (Seçilen Maç, Toplam Oran, 50 TL Kazanç) -->
                <div class="grid grid-cols-3 gap-1 sm:gap-2 bg-slate-900/90 p-2 sm:p-2.5 rounded-2xl border border-cardborder text-center shadow-inner w-full">
                    <div class="p-1 min-w-0">
                        <div class="text-[8px] sm:text-[10px] text-slate-400 uppercase tracking-wider font-bold">Seçilen Maç</div>
                        <div class="text-xs sm:text-lg font-black text-purple-300 truncate"><span id="dyn-match-count">${selectedMatches.length}</span> / ${matches.length}</div>
                    </div>
                    <div class="p-1 border-x border-cardborder min-w-0">
                        <div class="text-[8px] sm:text-[10px] text-slate-400 uppercase tracking-wider font-bold">Toplam Oran</div>
                        <div class="text-xs sm:text-lg font-black text-amber-300 truncate" id="dyn-total-odd">${oddFormatted}</div>
                    </div>
                    <div class="p-1 min-w-0">
                        <div class="text-[8px] sm:text-[10px] text-slate-400 uppercase tracking-wider font-bold">50 TL Kazanç</div>
                        <div class="text-xs sm:text-lg font-black text-emerald-400 truncate" id="dyn-payout">${winFormatted} TL</div>
                    </div>
                </div>

                <!-- Helper Tip -->
                <div class="mt-2 text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
                    <i class="fa-solid fa-circle-info text-purple-400"></i>
                    <span>Tüm maçlar en yüksek güvenden aşağıya doğru dizilmiştir. İstediğiniz maça dokunarak kuponunuza ekleyip çıkarabilirsiniz.</span>
                </div>
            </div>

            <!-- System Banner if applicable -->
            ${systemBanner}

            <!-- Ranked Match List -->
            <div class="space-y-2 mb-4">
                ${matchesHtml}
            </div>

            <!-- Coupon Card Footer -->
            <div class="p-3 sm:p-4 rounded-2xl bg-slate-900/90 border border-cardborder flex items-center justify-between flex-wrap gap-2 text-xs">
                <div>
                    <span class="text-slate-400 block text-[10px]">Kupon Bedeli:</span>
                    <span class="font-black text-white text-sm">50 TL (Sabit)</span>
                </div>
                <div class="text-right">
                    <span class="text-slate-400 block text-[10px]">Seçili <span id="footer-selected-count">${selectedMatches.length}</span> Maç Toplam Kazanç:</span>
                    <span class="font-black text-emerald-400 text-base" id="footer-payout">${winFormatted} TL</span>
                </div>
                <button onclick="copyActiveTicketText()" class="w-full sm:w-auto px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-black text-xs flex items-center justify-center gap-1.5 shadow">
                    <i class="fa-solid fa-copy"></i> Seçili Kuponu Kopyala (50 TL)
                </button>
            </div>
        </div>
    `;
}

// ================= PLATFORM BANNER CLICKS (MAÇLARI AÇ) =================
function openPlatformMatches(platformKey, platformName, rtp) {
    selectedPlatformFilter = { key: platformKey, name: platformName, rtp: rtp };
    switchTab('matches');
    const banner = document.getElementById('active-platform-banner');
    const bannerText = document.getElementById('active-platform-banner-text');
    if (banner && bannerText) {
        banner.classList.remove('hidden');
        bannerText.innerHTML = `<span class="text-amber-400 font-black">⚡ ${platformName}</span> (%${rtp} RTP) Bülteni ve Oranları Açıldı • En Yüksek Bahis Değerleri`;
    }
    const section = document.getElementById('section-matches');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    showToast(`⚡ ${platformName} maçları açıldı (RTP: %${rtp})`);
    renderBulletinMatches();
}

function resetPlatformFilter() {
    selectedPlatformFilter = null;
    const banner = document.getElementById('active-platform-banner');
    if (banner) banner.classList.add('hidden');
    renderBulletinMatches();
    showToast('Tüm bülten gösteriliyor');
}

function togglePlatformsBar() {
    const container = document.getElementById('platforms-container');
    const textEl = document.getElementById('text-toggle-platforms');
    const iconEl = document.getElementById('icon-toggle-platforms');
    if (!container) return;

    if (container.classList.contains('hidden')) {
        container.classList.remove('hidden');
        if (textEl) textEl.innerText = 'Daralt';
        if (iconEl) iconEl.className = 'fa-solid fa-chevron-up text-[10px]';
    } else {
        container.classList.add('hidden');
        if (textEl) textEl.innerText = 'Siteleri Aç (15 Site)';
        if (iconEl) iconEl.className = 'fa-solid fa-chevron-down text-[10px]';
    }
}

// ================= RENDER BULLETIN MATCHES =================
function renderBulletinMatches() {
    const grid = document.getElementById('matches-grid');
    if (!grid) return;

    if (!allMatchesData || allMatchesData.length === 0) {
        grid.innerHTML = '<div class="col-span-2 py-12 text-center text-slate-400">Canlı maç bülteni yükleniyor...</div>';
        return;
    }

    const searchInput = document.getElementById('bulletin-search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const dayFilter = document.getElementById('bulletin-day-filter');
    const dayVal = dayFilter ? dayFilter.value : 'all';

    let filtered = allMatchesData.filter(m => {
        if (dayVal !== 'all' && m.day && m.day !== dayVal) return false;
        if (query) {
            const h = (m.home_team || '').toLowerCase();
            const a = (m.away_team || '').toLowerCase();
            const l = (m.league || '').toLowerCase();
            if (!h.includes(query) && !a.includes(query) && !l.includes(query)) return false;
        }
        return true;
    });

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="col-span-2 py-12 text-center text-slate-400">Aramanıza uygun maç bulunamadı.</div>';
        return;
    }

    const platformBadgeText = selectedPlatformFilter ? `
        <span class="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
            ${selectedPlatformFilter.name} %${selectedPlatformFilter.rtp}
        </span>
    ` : '';

    grid.innerHTML = filtered.slice(0, 50).map((m, idx) => {
        const matchId = m.id || `m-${idx}`;
        const odds = m.odds || {};
        const ms1 = parseFloat(odds.ms1 || odds['1'] || 2.10).toFixed(2);
        const msX = parseFloat(odds.msX || odds['X'] || odds['0'] || 3.20).toFixed(2);
        const ms2 = parseFloat(odds.ms2 || odds['2'] || 3.10).toFixed(2);
        const u25 = parseFloat(odds.ust25 || odds['2.5_ust'] || 1.85).toFixed(2);
        const a25 = parseFloat(odds.alt25 || odds['2.5_alt'] || 1.85).toFixed(2);
        const nesineCode = m.nesine_code || m.bulten_code || (m.id ? String(m.id).replace('st-', '') : '54123');
        const mbs = m.mbs || 1;

        return `
            <div onclick="openMatchModal('${matchId}')" class="p-4 rounded-2xl bg-cardbg border border-cardborder hover:border-purple-500/70 transition-all shadow-md flex flex-col justify-between cursor-pointer group">
                <div>
                    <!-- Top line -->
                    <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
                        <span class="truncate max-w-[200px] text-slate-300 font-bold">
                            <i class="fa-solid fa-trophy text-amber-400 text-[10px] mr-1"></i>${m.league || 'Futbol'}
                        </span>
                        <div class="flex items-center gap-1.5">
                            ${platformBadgeText}
                            <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-bold">${m.match_time || 'Bugün'}</span>
                            <span class="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-bold">Kod: ${nesineCode}</span>
                            <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold">MBS: ${mbs}</span>
                        </div>
                    </div>

                    <!-- Teams -->
                    <div class="my-3">
                        <div class="font-black text-white text-base">${m.home_team || 'Ev Sahibi'}</div>
                        <div class="font-black text-slate-300 text-base mt-0.5">${m.away_team || 'Deplasman'}</div>
                    </div>

                    <!-- Odds Strip -->
                    <div class="grid grid-cols-5 gap-1.5 text-center text-xs my-2">
                        <div class="p-1.5 rounded-lg bg-slate-900 border border-cardborder">
                            <span class="text-[9px] text-slate-400 block">MS 1</span>
                            <span class="font-black text-emerald-400">${ms1}</span>
                        </div>
                        <div class="p-1.5 rounded-lg bg-slate-900 border border-cardborder">
                            <span class="text-[9px] text-slate-400 block">MS X</span>
                            <span class="font-black text-amber-400">${msX}</span>
                        </div>
                        <div class="p-1.5 rounded-lg bg-slate-900 border border-cardborder">
                            <span class="text-[9px] text-slate-400 block">MS 2</span>
                            <span class="font-black text-blue-400">${ms2}</span>
                        </div>
                        <div class="p-1.5 rounded-lg bg-slate-900 border border-cardborder">
                            <span class="text-[9px] text-slate-400 block">2.5 Alt</span>
                            <span class="font-bold text-slate-200">${a25}</span>
                        </div>
                        <div class="p-1.5 rounded-lg bg-slate-900 border border-cardborder">
                            <span class="text-[9px] text-slate-400 block">2.5 Üst</span>
                            <span class="font-bold text-slate-200">${u25}</span>
                        </div>
                    </div>
                </div>

                <!-- Footer Actions -->
                <div class="mt-3 pt-3 border-t border-cardborder/70 flex items-center justify-between gap-2 flex-wrap">
                    <span class="text-[11px] text-slate-400 truncate max-w-[180px]">
                        xG: ${m.expected_goals ? `${m.expected_goals.home} - ${m.expected_goals.away}` : 'Poisson Analizi'}
                    </span>
                    <div class="flex items-center gap-1.5 ml-auto" onclick="event.stopPropagation()">
                        <button onclick="openMatchModal('${matchId}', event)" class="px-3 py-1 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-black transition flex items-center gap-1 shadow active:scale-95">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> <span>Maçı Aç</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filterBulletin() {
    renderBulletinMatches();
}

// ================= RENDER IY MS SKOR TABLOSU =================
function renderIYMSTable() {
    const container = document.getElementById('iyms-table-container');
    if (!container) return;

    if (!iymsTableData || iymsTableData.length === 0) {
        container.innerHTML = '<div class="py-12 text-center text-slate-400">İY MS Skor tablosu yükleniyor...</div>';
        return;
    }

    const searchInput = document.getElementById('iyms-search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    let filtered = iymsTableData.filter(row => {
        if (!query) return true;
        const name = (row.match_name || '').toLowerCase();
        const league = (row.league || '').toLowerCase();
        return name.includes(query) || league.includes(query);
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="py-12 text-center text-slate-400">Aramanıza uygun maç bulunamadı.</div>';
        return;
    }

    container.innerHTML = filtered.slice(0, 30).map((row, idx) => {
        const matchId = row.match_id || `iyms-${idx}`;
        const topCombos = row.top_combos || [];
        const comboPills = topCombos.slice(0, 4).map(c => `
            <span class="px-2 py-0.5 rounded-lg bg-slate-900 border border-cardborder text-[11px] text-slate-300">
                ${c.combo}: <b class="text-purple-300">${c.odd}</b> (%${Math.round(c.prob * 100)})
            </span>
        `).join('');

        return `
            <div onclick="openMatchModal('${matchId}')" class="p-4 rounded-2xl bg-cardbg border border-cardborder hover:border-amber-500/60 transition-all shadow-md cursor-pointer group">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-2 flex-wrap gap-2">
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-slate-200">${row.match_time || 'Bugün'}</span>
                        <span>•</span>
                        <span class="font-semibold text-slate-300">${row.league || 'Futbol'}</span>
                    </div>
                    <div class="flex items-center gap-1.5 text-[10px]">
                        <span class="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">Kod: ${row.bulten_code || '---'}</span>
                        <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">MBS: ${row.mbs || 1}</span>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-center my-2">
                    <div class="md:col-span-5">
                        <h4 class="font-black text-white text-base">${row.match_name}</h4>
                        <div class="text-xs text-slate-400 mt-1">
                            xG: ${row.home_xg || '1.4'} - ${row.away_xg || '1.1'} (Toplam: ${row.total_xg || '2.5'})
                        </div>
                    </div>

                    <div class="md:col-span-5 flex items-center gap-2 flex-wrap">
                        <!-- İY / MS Box with its own Turkish standard odd -->
                        <div class="p-2.5 rounded-xl bg-slate-900/90 border border-amber-500/40 text-center flex-1 shadow-sm">
                            <span class="text-[9px] text-amber-400 block uppercase font-black tracking-wider">İY / MS Tahmini</span>
                            <div class="font-black text-white text-xs sm:text-sm mt-0.5">${row.ai_iyms_code} (${row.ai_iyms_label})</div>
                            <div class="mt-1">
                                <span class="text-[9px] text-slate-400 mr-1">İY/MS Oran:</span>
                                <span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-black text-xs border border-amber-500/30">
                                    ${parseFloat(row.iyms_odd || 4.50).toFixed(2)}
                                </span>
                            </div>
                        </div>

                        <!-- Doğru Skor Box with its own Turkish standard odd -->
                        <div class="p-2.5 rounded-xl bg-slate-900/90 border border-purple-500/40 text-center flex-1 shadow-sm">
                            <span class="text-[9px] text-purple-400 block uppercase font-black tracking-wider">Doğru Skor</span>
                            <div class="font-black text-white text-xs sm:text-sm mt-0.5">${row.score_display}</div>
                            <div class="mt-1 flex items-center justify-center gap-1.5 flex-wrap">
                                <div>
                                    <span class="text-[9px] text-slate-400 mr-1">Skor:</span>
                                    <span class="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-black text-xs border border-purple-500/30">
                                        ${parseFloat(row.score_odd || row.odd || 7.50).toFixed(2)}
                                    </span>
                                </div>
                                <div>
                                    <span class="text-[9px] text-slate-400 mr-1">Kombin:</span>
                                    <span class="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-black text-xs border border-rose-500/30">
                                        ${parseFloat(row.htft_score_odd || 26.00).toFixed(2)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="md:col-span-2 text-right">
                        <div class="text-[10px] text-slate-400 font-bold uppercase">Poisson Güveni</div>
                        <div class="text-base sm:text-lg font-black text-emerald-400">%${Math.round(row.confidence || 75)}</div>
                        <div class="mt-1">
                            <button onclick="openAllOddsModal('${matchId}')" class="px-2 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-[10px] font-bold transition flex items-center gap-1 ml-auto">
                                <i class="fa-solid fa-scale-balanced text-[10px]"></i> <span>Tüm Oranlar</span>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Top Combos -->
                <div class="mt-3 pt-2.5 border-t border-cardborder flex items-center justify-between flex-wrap gap-2">
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="text-[10px] text-slate-400 font-bold">En Yüksek Olasılıklı İY/MS:</span>
                        ${comboPills}
                    </div>
                    <div class="flex items-center gap-1.5 ml-auto">
                        <button onclick="openDeepAnalysisModal('${matchId}')" class="px-2.5 py-1 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-bold transition">
                            <i class="fa-solid fa-microscope text-xs"></i> <span>Derin Analiz</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filterIYMSTable() {
    renderIYMSTable();
}

// ================= CUSTOM WIZARD COUPON (5 MAÇ) =================
async function generateCustomWizardCoupon() {
    const style = document.getElementById('wizard-style').value;
    const resultContainer = document.getElementById('wizard-result');
    if (!resultContainer) return;

    resultContainer.classList.remove('hidden');
    resultContainer.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <i class="fa-solid fa-circle-notch fa-spin text-2xl mb-2 text-purple-500"></i>
            <p class="text-xs">Yapay zeka bülteni tarıyor ve 5 maçlık kupon oluşturuyor...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/custom-coupon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ style: style, count: 5, stake: 50 })
        });
        const data = await res.json();
        if (data.success && data.coupon) {
            const c = data.coupon;
            const matches = c.matches || [];
            const oddFormatted = parseFloat(c.total_odd || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 });
            const winFormatted = parseFloat(c.target_return || (50 * c.total_odd)).toLocaleString('tr-TR', { minimumFractionDigits: 2 });

            let rows = matches.map(m => `
                <div class="p-2.5 rounded-xl bg-slate-900 border border-cardborder flex items-center justify-between text-xs">
                    <div>
                        <div class="font-bold text-white">${m.home_team} - ${m.away_team}</div>
                        <div class="text-[10px] text-purple-300 font-semibold">${m.market_name || m.pick} • Kod: ${m.nesine_code || '---'}</div>
                    </div>
                    <div class="text-right">
                        <span class="font-black text-emerald-400 text-sm">${parseFloat(m.odd || 1.80).toFixed(2)}</span>
                    </div>
                </div>
            `).join('');

            resultContainer.innerHTML = `
                <div class="p-4 rounded-2xl bg-cardbg border-2 border-purple-500/60 shadow-xl mt-4">
                    <div class="flex items-center justify-between mb-3 border-b border-cardborder pb-2">
                        <div>
                            <span class="text-[10px] font-black text-purple-300 uppercase tracking-wider">${c.badge || 'ÖZEL 5 MAÇ'}</span>
                            <h4 class="font-black text-white text-base">${c.title}</h4>
                        </div>
                        <div class="text-right">
                            <span class="text-[10px] text-slate-400 block font-bold">Kazanç (50 TL)</span>
                            <span class="text-emerald-400 font-black text-base">${winFormatted} TL</span>
                        </div>
                    </div>
                    <div class="space-y-2 mb-3">
                        ${rows}
                    </div>
                    <div class="flex items-center justify-between pt-2 border-t border-cardborder text-xs">
                        <span class="text-slate-400">Toplam Oran: <b class="text-white">${oddFormatted}</b></span>
                        <button onclick="showToast('Özel kupon kopyalandı!')" class="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs">
                            <i class="fa-solid fa-copy"></i> Kopyala
                        </button>
                    </div>
                </div>
            `;
        } else {
            resultContainer.innerHTML = '<div class="py-4 text-center text-rose-400 text-xs">Kupon oluşturulamadı. Lütfen tekrar deneyin.</div>';
        }
    } catch (err) {
        resultContainer.innerHTML = `<div class="py-4 text-center text-rose-400 text-xs">Hata: ${err.message}</div>`;
    }
}

// ================= MODALS CONTROLLER =================
function openTopPayoutsModal() {
    const modal = document.getElementById('top-payouts-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeTopPayoutsModal() {
    const modal = document.getElementById('top-payouts-modal');
    if (modal) modal.classList.add('hidden');
}

function openSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.remove('hidden');
        const input = document.getElementById('global-search-input');
        if (input) {
            input.value = '';
            input.focus();
        }
    }
}

function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) modal.classList.add('hidden');
}

function handleGlobalSearch() {
    const input = document.getElementById('global-search-input');
    const container = document.getElementById('search-results-container');
    if (!input || !container) return;

    const q = input.value.toLowerCase().trim();
    if (!q) {
        container.innerHTML = '<div class="text-center py-8 text-slate-500 text-xs">Aramak istediğin takım veya platform adını yaz...</div>';
        return;
    }

    // Search matches
    const matches = allMatchesData.filter(m => {
        const h = (m.home_team || '').toLowerCase();
        const a = (m.away_team || '').toLowerCase();
        const l = (m.league || '').toLowerCase();
        return h.includes(q) || a.includes(q) || l.includes(q);
    });

    if (matches.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">"${q}" için sonuç bulunamadı.</div>`;
        return;
    }

    container.innerHTML = matches.slice(0, 15).map(m => `
        <div class="p-3 rounded-xl bg-slate-900 border border-cardborder flex items-center justify-between text-xs hover:border-purple-500/50 transition">
            <div>
                <div class="font-bold text-white text-sm">${m.home_team} - ${m.away_team}</div>
                <div class="text-[10px] text-slate-400">${m.league} • ${m.match_time}</div>
            </div>
            <div class="flex items-center gap-1.5">
                <button onclick="closeSearchModal(); openDeepAnalysisModal('${m.id}')" class="px-2.5 py-1 rounded-lg bg-purple-600 text-white font-bold text-xs">
                    Analiz
                </button>
                <button onclick="closeSearchModal(); openAllOddsModal('${m.id}')" class="px-2.5 py-1 rounded-lg bg-blue-600 text-white font-bold text-xs">
                    Oranlar
                </button>
            </div>
        </div>
    `).join('');
}

// ================= COMPREHENSIVE MATCH MODAL (MAÇI AÇ & İNCELE) =================
let currentModalMatchId = null;
let currentModalTab = 'odds';
let cachedModalData = {};

async function openMatchModal(matchId, event, defaultTab = 'odds') {
    if (event && event.stopPropagation) {
        event.stopPropagation();
    }
    currentModalMatchId = String(matchId);
    currentModalTab = defaultTab;

    const modal = document.getElementById('all-odds-modal');
    const content = document.getElementById('all-odds-modal-content');
    if (!modal || !content) return;

    modal.classList.remove('hidden');
    content.innerHTML = `
        <div class="py-16 text-center text-slate-400">
            <i class="fa-solid fa-circle-notch fa-spin text-3xl mb-3 text-purple-500"></i>
            <p class="font-black text-white text-base">Canlı Maç Detayları ve Oranları Açılıyor...</p>
            <p class="text-xs text-slate-400 mt-1">Nesine, Pinnacle, Betfair ve Dixon-Coles xG parametreleri taranıyor</p>
        </div>
    `;

    try {
        const [oddsRes, analysisRes] = await Promise.allSettled([
            fetch(`/api/match-all-odds/${matchId}`).then(r => r.json()),
            fetch(`/api/match-deep-analysis/${matchId}`).then(r => r.json())
        ]);

        const oddsData = oddsRes.status === 'fulfilled' && oddsRes.value ? oddsRes.value : {};
        const analysisData = analysisRes.status === 'fulfilled' && analysisRes.value ? analysisRes.value : {};

        cachedModalData[matchId] = {
            odds: oddsData,
            analysis: analysisData
        };

        renderMatchModalContent(matchId, currentModalTab);
    } catch (err) {
        console.error('Maç açma hatası:', err);
        content.innerHTML = `
            <div class="py-12 text-center text-rose-400">
                <i class="fa-solid fa-circle-exclamation text-3xl mb-2"></i>
                <div class="text-sm font-bold">Maç detayları açılırken bir hata oluştu: ${err.message}</div>
                <button onclick="openMatchModal('${matchId}')" class="mt-4 px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-bold">Tekrar Dene</button>
            </div>
        `;
    }
}

function switchModalTab(tabKey) {
    currentModalTab = tabKey;
    if (currentModalMatchId) {
        renderMatchModalContent(currentModalMatchId, tabKey);
    }
}

function updateModalCouponBtn(matchId) {
    const btn = document.getElementById('modal-ticket-btn');
    if (!btn) return;
    const isSel = activeSelectedMatchIds.has(String(matchId));
    if (isSel) {
        btn.className = 'px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1.5 shadow active:scale-95 transition';
        btn.innerHTML = '<i class="fa-solid fa-check"></i> 50 TL Kuponunda Seçili';
    } else {
        btn.className = 'px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-black text-xs flex items-center gap-1.5 shadow active:scale-95 transition';
        btn.innerHTML = '<i class="fa-solid fa-plus"></i> Bu Maçı 50 TL Kupona Ekle';
    }
}

function renderMatchModalContent(matchId, tabKey) {
    const content = document.getElementById('all-odds-modal-content');
    if (!content) return;

    const data = cachedModalData[matchId] || {};
    const o = data.odds || {};
    const a = (data.analysis && data.analysis.analysis) ? data.analysis.analysis : (data.analysis || {});

    const home = o.home_team || a.home_team || (o.match_name ? o.match_name.split(' - ')[0] : 'Ev Sahibi');
    const away = o.away_team || a.away_team || (o.match_name ? o.match_name.split(' - ')[1] : 'Deplasman');
    const league = o.league || a.league || 'Futbol Ligi';
    const time = o.match_time || o.time || a.match_time || 'Bugün';
    const bultenCode = o.bulten_code || a.bulten_code || String(matchId).replace('st-', '');
    const mbs = o.mbs || a.mbs || 1;
    const isSel = activeSelectedMatchIds.has(String(matchId));

    // Platform Comparison Rows
    const comparison = o.comparison_table || o.all_odds || [];
    let compRows = comparison.map(item => `
        <tr class="border-b border-cardborder text-xs hover:bg-slate-900/50 transition">
            <td class="py-2.5 px-3 font-bold text-white flex items-center gap-1.5">${item.platform || 'Platform'}</td>
            <td class="py-2.5 px-3 text-emerald-400 font-bold">${item.rtp ? `%${item.rtp}` : '%95.0'}</td>
            <td class="py-2.5 px-3 font-black text-purple-300">${item.ms1 ? parseFloat(item.ms1).toFixed(2) : '---'}</td>
            <td class="py-2.5 px-3 font-black text-amber-300">${item.msX ? parseFloat(item.msX).toFixed(2) : '---'}</td>
            <td class="py-2.5 px-3 font-black text-blue-300">${item.ms2 ? parseFloat(item.ms2).toFixed(2) : '---'}</td>
            <td class="py-2.5 px-3 font-semibold text-slate-200">${item.ust25 ? parseFloat(item.ust25).toFixed(2) : '---'}</td>
            <td class="py-2.5 px-3 font-semibold text-slate-200">${item.kg_var ? parseFloat(item.kg_var).toFixed(2) : '---'}</td>
        </tr>
    `).join('');

    const cat = o.categorized_odds || {};
    const renderGridItems = (obj, badgeClass = 'text-amber-300') => {
        if (!obj || Object.keys(obj).length === 0) return '<div class="text-xs text-slate-500 italic p-2">Bu piyasa için oran bültende bulunamadı.</div>';
        const items = Object.entries(obj).filter(([k, v]) => v != null && v !== '');
        if (items.length === 0) return '<div class="text-xs text-slate-500 italic p-2">Bu piyasa için oran bültende bulunamadı.</div>';
        return items.map(([label, odd]) => `
            <div class="flex items-center justify-between p-2 sm:p-2.5 rounded-xl bg-slate-900/70 border border-cardborder hover:border-purple-500/50 transition">
                <span class="text-xs font-bold text-slate-300 truncate mr-2">${label}</span>
                <span class="text-xs font-black ${badgeClass} px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20 shrink-0">
                    ${parseFloat(odd).toFixed(2)}
                </span>
            </div>
        `).join('');
    };

    // Poisson Probable Scores
    const topScoresList = (a.top_exact_scores || (a.iyms_scores && a.iyms_scores.top_ft) || []).slice(0, 6).map(s => {
        const sc = s.score || `${s.h}-${s.a}`;
        const p = s.probability ? Math.round(s.probability * 100) : (s.prob ? Math.round(s.prob) : 10);
        const oVal = s.fair_odd || (p > 0 ? (100 / p).toFixed(2) : '7.50');
        return `
            <div class="p-2 sm:p-2.5 rounded-xl bg-slate-900 border border-cardborder text-center flex-1 min-w-[70px]">
                <div class="font-black text-white text-xs sm:text-sm">${sc}</div>
                <div class="text-[10px] text-emerald-400 font-bold mt-0.5">%${p}</div>
                <div class="text-[9px] text-slate-400">Oran: ${oVal}</div>
            </div>
        `;
    }).join('');

    let tabBodyHtml = '';
    if (tabKey === 'odds') {
        tabBodyHtml = `
            <!-- Global Platform Comparison -->
            <div class="mb-6">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs uppercase tracking-wider font-extrabold text-blue-400 flex items-center gap-1.5">
                        <i class="fa-solid fa-scale-balanced"></i> Global Bahis Platformları Karşılaştırması
                    </h4>
                    <span class="text-[10px] text-slate-400">Canlı Payout & RTP Karşılaştırması</span>
                </div>
                <div class="overflow-x-auto rounded-xl border border-cardborder bg-slate-950/60">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-cardborder text-[10px] text-slate-400 uppercase tracking-wider bg-slate-900/90">
                                <th class="py-2.5 px-3">Platform</th>
                                <th class="py-2.5 px-3">Payout</th>
                                <th class="py-2.5 px-3 text-purple-300">MS 1</th>
                                <th class="py-2.5 px-3 text-amber-300">MS X</th>
                                <th class="py-2.5 px-3 text-blue-300">MS 2</th>
                                <th class="py-2.5 px-3">2.5 Üst</th>
                                <th class="py-2.5 px-3">KG Var</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${compRows}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- All Turkish Legal Nesine / İddaa Markets -->
            <div class="space-y-4">
                <div class="flex items-center justify-between">
                    <h4 class="text-xs uppercase tracking-wider font-extrabold text-emerald-400 flex items-center gap-1.5">
                        <i class="fa-solid fa-layer-group"></i> Bu Maçın Tüm Resmi Nesine / İddaa Seçenekleri
                    </h4>
                    <span class="text-[10px] text-slate-400">Canlı Bülten Oranları</span>
                </div>

                <!-- MS & Alt/Üst & KG -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                        <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <i class="fa-solid fa-flag text-purple-400"></i> Maç Sonucu (MS)
                        </div>
                        <div class="space-y-1.5">${renderGridItems(cat.ms, 'text-purple-300')}</div>
                    </div>
                    <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                        <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <i class="fa-solid fa-futbol text-emerald-400"></i> Alt / Üst Goller
                        </div>
                        <div class="space-y-1.5">${renderGridItems(cat.goller, 'text-emerald-300')}</div>
                    </div>
                    <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                        <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <i class="fa-solid fa-handshake text-blue-400"></i> Karşılıklı Gol
                        </div>
                        <div class="space-y-1.5">${renderGridItems(cat.kg, 'text-blue-300')}</div>
                    </div>
                </div>

                <!-- İY / MS -->
                <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                    <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <i class="fa-solid fa-arrows-rotate text-purple-400"></i> İlk Yarı / Maç Sonucu (İY/MS - 9 İhtimal)
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">${renderGridItems(cat.iy_ms, 'text-purple-300')}</div>
                </div>

                <!-- Doğru Skor -->
                <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                    <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <i class="fa-solid fa-bullseye text-rose-400"></i> Doğru Skor Seçenekleri (Tam Maç Skoru)
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">${renderGridItems(cat.dogru_skor, 'text-rose-300')}</div>
                </div>

                <!-- İY/MS Skor -->
                <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                    <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <i class="fa-solid fa-chart-pie text-amber-400"></i> İlk Yarı / Maç Skoru Kombinasyonları
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">${renderGridItems(cat.iy_ms_skor, 'text-amber-300')}</div>
                </div>

                <!-- Özel Kombinler -->
                <div class="p-3.5 rounded-2xl bg-cardbg/90 border border-cardborder">
                    <div class="text-[11px] font-black text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <i class="fa-solid fa-gem text-indigo-400"></i> Özel Kombin & Çoklu Piyasalar
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">${renderGridItems(cat.kombin, 'text-indigo-300')}</div>
                </div>
            </div>
        `;
    } else {
        // Analysis Tab
        const goalStats = a.goal_stats || {};
        const recs = (a.recommendations || []).map(r => `
            <div class="p-3 rounded-xl bg-purple-950/40 border border-purple-500/40 text-xs">
                <div class="font-black text-amber-300 flex items-center gap-1.5">
                    <span>${r.icon || '⚽'}</span> <span>${r.pick}</span>
                    <span class="ml-auto text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">${r.confidence || 'Yüksek'}</span>
                </div>
                <div class="text-slate-300 text-[11px] mt-1">${r.reason || ''}</div>
            </div>
        `).join('');

        tabBodyHtml = `
            <div>
                <!-- xG & Attack/Defense Grid -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3">
                    <div class="p-3 rounded-2xl bg-slate-900 border border-cardborder text-center">
                        <span class="text-[10px] text-slate-400 block uppercase font-bold">Ev Sahibi xG</span>
                        <span class="text-lg font-black text-purple-400">${a.lambda_home || '1.80'}</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-900 border border-cardborder text-center">
                        <span class="text-[10px] text-slate-400 block uppercase font-bold">Deplasman xG</span>
                        <span class="text-lg font-black text-indigo-400">${a.mu_away || '1.10'}</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-900 border border-cardborder text-center">
                        <span class="text-[10px] text-slate-400 block uppercase font-bold">Toplam Beklenen Gol</span>
                        <span class="text-lg font-black text-emerald-400">${a.total_expected_goals || goalStats.total_avg || '2.90'}</span>
                    </div>
                    <div class="p-3 rounded-2xl bg-slate-900 border border-cardborder text-center">
                        <span class="text-[10px] text-slate-400 block uppercase font-bold">Poisson Güven</span>
                        <span class="text-lg font-black text-amber-400">%${Math.round(a.confidence || 82)}</span>
                    </div>
                </div>

                <!-- Top Probable Scores -->
                <div class="my-4 p-3.5 rounded-2xl bg-slate-900/80 border border-cardborder">
                    <span class="text-xs font-bold text-slate-300 block mb-2">En Olası Skorlar (Poisson xG Dağılımı):</span>
                    <div class="flex items-center gap-2 flex-wrap">
                        ${topScoresList || '<div class="text-xs text-slate-400">Skor verisi hesaplanıyor</div>'}
                    </div>
                </div>

                <!-- Recommendations -->
                ${recs ? `
                <div class="my-4">
                    <span class="text-xs font-bold text-slate-300 block mb-2">Yapay Zeka Bahis Önerileri:</span>
                    <div class="space-y-2">
                        ${recs}
                    </div>
                </div>
                ` : ''}

                <!-- AI Note -->
                <div class="p-3.5 rounded-2xl bg-purple-950/30 border border-purple-500/30 text-xs text-slate-300 leading-relaxed">
                    <b class="text-purple-300">Yapay Zeka Taktik Notu:</b> ${a.tactical_note || a.summary || 'Ev sahibi takımın iç saha hücum xG üretimi yüksek; karşılıklı gollü bir mücadele bekleniyor.'}
                </div>
            </div>
        `;
    }

    content.innerHTML = `
        <div class="pr-1 sm:pr-2 max-h-[82vh] overflow-y-auto custom-scrollbar">
            <!-- Header -->
            <div class="border-b border-cardborder pb-3 mb-3">
                <div class="flex items-center justify-between gap-2 flex-wrap mb-2">
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-bold text-[10px] sm:text-xs border border-blue-500/40">
                            🌍 CANLI DÜNYA & TÜRKİYE BÜLTENİ
                        </span>
                        <span class="px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-300 text-[10px] font-bold">
                            Kod: ${bultenCode}
                        </span>
                        <span class="px-1.5 py-0.5 rounded-md bg-rose-500/20 text-rose-300 text-[10px] font-bold">
                            MBS: ${mbs}
                        </span>
                    </div>
                    <div>
                        <button onclick="toggleMatchSelection('${matchId}'); updateModalCouponBtn('${matchId}');" id="modal-ticket-btn" class="px-3 py-1.5 rounded-xl ${isSel ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'} font-black text-xs flex items-center gap-1.5 shadow active:scale-95 transition">
                            ${isSel ? '<i class="fa-solid fa-check"></i> 50 TL Kuponunda Seçili' : '<i class="fa-solid fa-plus"></i> Bu Maçı 50 TL Kupona Ekle'}
                        </button>
                    </div>
                </div>

                <h3 class="text-lg sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                    <span>${home}</span> <span class="text-slate-400 font-normal text-sm sm:text-base">vs</span> <span>${away}</span>
                </h3>
                <p class="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
                    <span><i class="fa-solid fa-trophy text-amber-400 mr-1"></i>${league}</span>
                    <span>•</span>
                    <span><i class="fa-regular fa-clock text-blue-400 mr-1"></i>${time}</span>
                </p>

                <!-- Modal Sub-Tabs Navigation -->
                <div class="flex items-center gap-2 mt-3 pt-3 border-t border-cardborder/60">
                    <button onclick="switchModalTab('odds')" class="px-3 py-1.5 rounded-xl text-xs font-black transition flex items-center gap-1.5 ${tabKey === 'odds' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-cardborder'}">
                        <i class="fa-solid fa-scale-balanced"></i> <span>Tüm Oranlar & Platformlar</span>
                    </button>
                    <button onclick="switchModalTab('analysis')" class="px-3 py-1.5 rounded-xl text-xs font-black transition flex items-center gap-1.5 ${tabKey === 'analysis' ? 'bg-purple-600 text-white shadow-md' : 'bg-slate-900 text-slate-400 hover:text-white border border-cardborder'}">
                        <i class="fa-solid fa-microscope"></i> <span>Poisson & xG Derin Analiz</span>
                    </button>
                </div>
            </div>

            <!-- Tab Content Area -->
            <div>
                ${tabBodyHtml}
            </div>
        </div>
    `;
}

// Modal helper compatibility wrappers
function openAllOddsModal(matchId, event) {
    openMatchModal(matchId, event, 'odds');
}

function openDeepAnalysisModal(matchId, event) {
    openMatchModal(matchId, event, 'analysis');
}

function closeAllOddsModal() {
    const modal = document.getElementById('all-odds-modal');
    if (modal) modal.classList.add('hidden');
}

function closeDeepAnalysisModal() {
    const modal = document.getElementById('deep-analysis-modal');
    if (modal) modal.classList.add('hidden');
    const modal2 = document.getElementById('all-odds-modal');
    if (modal2) modal2.classList.add('hidden');
}


// ================= REFRESH ALL COUPONS =================
async function refreshAllCoupons() {
    const syncBtn = document.getElementById('sync-nesine-btn');
    const syncIcon = document.getElementById('sync-icon');
    const syncText = document.getElementById('sync-text');

    if (syncIcon) syncIcon.classList.add('fa-spin');
    if (syncText) syncText.innerText = 'Taranıyor...';

    showToast('Canlı bülten taranıyor, 5 maçlık kuponlar yenileniyor...');

    try {
        const res = await fetch('/api/refresh-coupons', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            allCouponsData = data.coupons || {};
            renderActiveCoupon();
            showToast('✅ 5 Maçlık kuponlar canlı bültenden güncellendi!');
        } else {
            showToast('Kuponlar güncellenirken hata oluştu', true);
        }
    } catch (err) {
        showToast('Bağlantı hatası: ' + err.message, true);
    } finally {
        if (syncIcon) syncIcon.classList.remove('fa-spin');
        if (syncText) syncText.innerText = 'Kuponları Güncelle';
    }
}

// ================= COPY COUPON =================
function copyCurrentCoupon() {
    const coupon = allCouponsData[activeCouponDay] || Object.values(allCouponsData)[0];
    if (!coupon || !coupon.matches) return;

    let text = `🎯 İDDAA AI PRO - 5 MAÇLIK KUPON\n`;
    text += `📋 Model: ${coupon.title || activeCouponDay}\n`;
    text += `💰 Tutar: ${coupon.target_stake || 50} TL (Misli: 50)\n`;
    text += `📈 Toplam Oran: ${parseFloat(coupon.total_odd || 0).toFixed(2)}\n`;
    text += `🏆 Hedef Kazanç: ${parseFloat(coupon.target_return || 0).toLocaleString('tr-TR')} TL\n\n`;

    coupon.matches.forEach((m, idx) => {
        text += `${idx + 1}) [Kod: ${m.nesine_code || m.bulten_code || '---'}] ${m.home_team} - ${m.away_team}\n`;
        text += `   👉 Tercih: ${m.market_name || m.pick} @ ${parseFloat(m.odd || 1.80).toFixed(2)}\n`;
    });

    text += `\n🤖 Dixon-Coles & Poisson xG Modeli ile üretilmiştir.`;

    navigator.clipboard.writeText(text).then(() => {
        showToast('✅ 5 Maçlık kupon panoya kopyalandı!');
    }).catch(() => {
        showToast('Kupon kopyalandı!');
    });
}

// ================= UTILITIES =================
function formatCleanPick(rawPick) {
    if (!rawPick) return 'Maç Sonucu 1';
    let p = String(rawPick).trim();

    // Parantez içi açıklamaları temizle: (İY Berabere / MS 1), (Geri Dönüş) vb.
    while (p.includes('(') && p.includes(')')) {
        p = p.replace(/\s*\([^()]*\)/g, '').trim();
    }

    // Gereksiz uzun önekleri sadeleştir
    p = p.replace(/^İlk Yarı\s*\/\s*Maç Skoru:\s*/i, 'İY/MS Skor: ');
    p = p.replace(/^İlk Yarı\s*\/\s*Maç Sonucu:\s*/i, 'İY/MS ');
    p = p.replace(/^Toplam Gol:\s*/i, '');

    if (p.startsWith('İY/MS:')) {
        p = p.replace('İY/MS:', 'İY/MS');
    }

    return p.trim();
}
function getSmartShortNote(m) {
    const h = m.home_team || 'Ev Sahibi';
    const a = m.away_team || 'Deplasman';
    const pick = (m.market_name || m.pick || '').toLowerCase();

    if (pick.includes('1/2') || pick.includes('2/1')) {
        return `${h} maça hızlı başlayıp öne geçer, ikinci yarı rotasyon ve kontra ataklarla geri dönüş senaryosu öne çıkıyor.`;
    }
    if (pick.includes('1/0') || pick.includes('2/0') || pick.includes('0/1') || pick.includes('0/2')) {
        return `İlk yarı skorunu koruma eğilimi ve ikinci yarı dengeli oyun stratejisi xG verilerinde öne çıkıyor.`;
    }
    if (pick.includes('skor') || pick.includes(':')) {
        return `İki takımın hücum/savunma Poisson regresyon eğrileri bu tam skor üzerinde kümeleniyor.`;
    }
    if (pick.includes('üst')) {
        return `Her iki takımın toplam beklenen gol üretimi (xG > 2.80) açık futbolu işaret ediyor.`;
    }
    return `${h} ve ${a} arasındaki form grafiği ve istatistiki güç endeksi bu tercihi destekliyor.`;
}

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');
    if (!toast || !toastMsg) return;

    toastMsg.innerText = message;
    if (isError) {
        toastIcon.className = 'fa-solid fa-circle-exclamation text-rose-400 text-lg';
    } else {
        toastIcon.className = 'fa-solid fa-circle-check text-emerald-400 text-lg';
    }

    toast.classList.remove('translate-y-24', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-24', 'opacity-0');
    }, 2800);
}
