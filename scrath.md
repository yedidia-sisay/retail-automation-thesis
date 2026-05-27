<!DOCTYPE html>

<html class="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>VisionPOS AI - AI Retail Checkout</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">tailwind.config = {darkMode: "class", theme: {extend: {colors: {"on-primary-container": "#fffbff", "surface-container-high": "#ffe2dd", "primary-fixed": "#ffdad6", secondary: "#ab332c", "on-secondary": "#ffffff", "secondary-fixed-dim": "#ffb4ab", "on-primary-fixed-variant": "#93000a", "outline-variant": "#e7bdb7", "surface-variant": "#fddbd6", "status-info": "#3B82F6", "status-error": "#EF4444", "surface-bright": "#fff8f7", "on-secondary-fixed-variant": "#8a1b18", "on-error-container": "#93000a", "page-bg": "#C2BFB0", "on-error": "#ffffff", "surface-tint": "#c00011", "on-secondary-container": "#700408", "tertiary-fixed": "#c9e6ff", "on-background": "#291714", "weighted-accent": "#0EA5E9", "secondary-fixed": "#ffdad6", "inverse-primary": "#ffb4ab", "surface-container-lowest": "#ffffff", "surface-container-highest": "#fddbd6", "surface-dim": "#f4d3ce", error: "#ba1a1a", "inverse-surface": "#402b28", "tertiary-container": "#007cb3", "status-warning": "#F59E0B", "on-primary": "#ffffff", "secondary-container": "#ff7164", primary: "#bb0010", "on-tertiary-fixed": "#001e2f", outline: "#926f6a", "surface-container-low": "#fff0ee", "panel-bg": "#FFFFFF", "primary-container": "#e41f22", "on-surface": "#291714", "on-tertiary": "#ffffff", "on-tertiary-fixed-variant": "#004b6f", "on-surface-variant": "#5d3f3c", "on-secondary-fixed": "#410002", "primary-fixed-dim": "#ffb4ab", "on-primary-fixed": "#410002", surface: "#fff8f7", "error-container": "#ffdad6", tertiary: "#00628e", "status-neutral": "#94A3B8", "inverse-on-surface": "#ffedea", "surface-container": "#ffe9e6", background: "#fff8f7", "tertiary-fixed-dim": "#8bceff", "on-tertiary-container": "#fcfcff", "status-success": "#10B981"}, borderRadius: {DEFAULT: "0.25rem", lg: "0.5rem", xl: "0.75rem", full: "9999px"}, spacing: {"container-margin": "1.5rem", "item-gap": "0.5rem", "panel-padding": "1.25rem", "stack-gap": "0.75rem", gutter: "1rem"}, fontFamily: {"body-base": ["Inter"], "stat-lg": ["Inter"], "headline-md": ["Inter"], "label-bold": ["Inter"], "body-sm": ["Inter"], "display-lg": ["Inter"]}, fontSize: {"body-base": ["16px", {lineHeight: "24px", fontWeight: "400"}], "stat-lg": ["24px", {lineHeight: "32px", fontWeight: "700"}], "headline-md": ["20px", {lineHeight: "28px", fontWeight: "600"}], "label-bold": ["12px", {lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "700"}], "body-sm": ["14px", {lineHeight: "20px", fontWeight: "400"}], "display-lg": ["30px", {lineHeight: "38px", letterSpacing: "-0.02em", fontWeight: "700"}]}}}};</script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
        }
        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
    </style>
</head>
<body class="bg-page-bg font-body-base text-on-surface min-h-screen">
<!-- TopAppBar -->
<header class="fixed top-0 left-0 right-0 z-50 flex justify-between items-center w-full px-container-margin py-3 bg-surface border-b border-outline-variant shadow-sm">
<div class="flex items-center gap-6">
<div class="flex flex-col">
<span class="font-display-lg text-display-lg font-black text-primary tracking-tight">VisionPOS AI</span>
<span class="font-label-bold text-label-bold text-on-surface-variant">Session #1042</span>
</div>
<div class="h-8 w-[1px] bg-outline-variant mx-2"></div>
<div class="flex items-center gap-4">
<div class="flex flex-col">
<span class="font-label-bold text-label-bold text-secondary uppercase tracking-wider">Cashier</span>
<span class="font-headline-md text-headline-md text-on-surface">Hana</span>
</div>
<div class="bg-status-success/10 text-status-success px-3 py-1 rounded-full flex items-center gap-1">
<span class="w-2 h-2 rounded-full bg-status-success"></span>
<span class="font-label-bold text-label-bold uppercase">Status: Open</span>
</div>
</div>
</div>
<div class="flex items-center gap-stack-gap">
<button class="bg-primary text-on-primary px-4 py-2 rounded-lg font-label-bold text-label-bold hover:brightness-110 active:scale-95 transition-all flex items-center gap-2">
<span class="material-symbols-outlined">add_circle</span>
                New Session
            </button>
<button class="border border-error text-error px-4 py-2 rounded-lg font-label-bold text-label-bold hover:bg-error/5 active:scale-95 transition-all flex items-center gap-2">
<span class="material-symbols-outlined">cancel</span>
                Cancel Session
            </button>
<div class="flex items-center gap-2 ml-4">
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-primary transition-colors">notifications_active</span>
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-primary transition-colors">help_outline</span>
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-primary transition-colors">settings</span>
</div>
</div>
</header>
<main class="pt-[88px] p-gutter grid grid-cols-12 gap-gutter h-[calc(100vh-88px)] overflow-hidden">
<!-- Left Column: Camera Feeds (Vertical Aspect) -->
<section class="col-span-12 md:col-span-3 flex flex-col gap-gutter h-full">
<div class="flex-1 flex flex-col gap-2">
<div class="flex-1 relative bg-black rounded-xl overflow-hidden group">
<img class="w-full h-full object-cover" data-alt="A vertical camera view of a supermarket conveyor belt." src="https://lh3.googleusercontent.com/aida-public/AB6AXuClUFcv5hpoKkJBMdk0xpLaegaXZhW4PgIInQCwxGxqGBVbFwvVqIQyLn2dukP_F5dVZ3SyHj54ySA31D6LIemlEVq-wl9IcFGKUtLazuneNQyOD-ROlkL2JmB0Ag_QjondxX1vB_uuvOjTHxEr1Afz-ml026vRfBBRPIKthOkkpeeLTv27zAyw6VoIPgQNsHbH8CgGFLPbGG9PlxHQdVFUBowLrJpI24QkhU8yYpGBOdwuMEIK6EZnF6DrfJtt2Hb_VqRrelM9kL7L"/>
<div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent"></div>
<div class="absolute bottom-4 left-4">
<span class="bg-status-error text-on-error px-2 py-0.5 rounded text-[10px] font-bold uppercase animate-pulse">Live</span>
</div>
</div>
<button class="w-full bg-primary text-on-primary py-3 rounded-xl font-label-bold text-label-bold hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
<span class="material-symbols-outlined">photo_camera</span>
                    Capture Packaged
                </button>
</div>
<div class="flex-1 flex flex-col gap-2">
<div class="flex-1 relative bg-black rounded-xl overflow-hidden">
<img class="w-full h-full object-cover" data-alt="A vertical camera view of a digital produce scale." src="https://lh3.googleusercontent.com/aida-public/AB6AXuD41c_3doVzyFQKOfChMtPyeRt_5A5OU65qe9nrboXUPyWGDDDo1cqVKJQ0kNxDU_YOPH7s40WKB4XBS4LUb6pTbxCmmeYUuZpYK-RaBB9vYmtLCRYLQJocA0uWfvousOAgTRfoo2Fh0iSBAInKemw50bAnZpohwE3GshJIpkn8KCRpt52airLKvuwWy8-CpVCkxGHxJAOEOthjNO78GbJScjUKJtrPQ0806WnHwYmUJrHH3jzb0UcqiR11OKcmW9XIXepWLXixqMnr"/>
<div class="absolute top-4 left-4 bg-black/60 backdrop-blur-md text-white px-3 py-1.5 rounded-lg text-sm font-mono border border-white/10">0.00 kg</div>
</div>
<button class="w-full bg-secondary-container text-on-secondary-container py-3 rounded-xl font-label-bold text-label-bold hover:brightness-105 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
<span class="material-symbols-outlined">scale</span>
                    Capture Weighted
                </button>
</div>
</section>
<!-- Middle Column: Review (Simplified Cards) -->
<section class="col-span-12 md:col-span-6 flex flex-col gap-stack-gap h-full overflow-y-auto pr-2 custom-scrollbar">
<div class="space-y-4">
<div class="flex justify-between items-center px-2">
<h3 class="font-label-bold text-label-bold text-secondary uppercase tracking-[0.2em]">Packaged Detection</h3>
<button class="bg-status-success text-on-primary px-6 py-2.5 rounded-xl font-label-bold text-label-bold shadow-lg hover:brightness-110 active:scale-95 transition-all">
                        Accept All Matches
                    </button>
</div>
<!-- Card: Coca Cola -->
<div class="bg-panel-bg px-panel-padding py-3 rounded-xl shadow-sm border border-outline-variant hover:border-primary/40 transition-all flex items-center justify-between">
<div class="flex flex-col">
<h4 class="font-headline-md text-on-surface">Coca Cola 500ml</h4>
<span class="text-status-success font-label-bold text-[10px] uppercase">91% Confidence</span>
</div>
<div class="flex items-center gap-3">
<select class="bg-surface-container-low border-none rounded-lg py-1.5 px-3 font-bold text-sm focus:ring-0">
<option>1 Qty</option>
<option>2 Qty</option>
<option>3 Qty</option>
<option>4 Qty</option>
</select>
<button class="p-2 text-error hover:bg-error/10 rounded-lg transition-colors">
<span class="material-symbols-outlined">delete</span>
</button>
</div>
</div>
<!-- Card: Lays Chips -->
<div class="bg-panel-bg px-panel-padding py-3 rounded-xl shadow-sm border-2 border-status-warning hover:border-status-warning/60 transition-all flex items-center justify-between">
<div class="flex flex-col">
<h4 class="font-headline-md text-on-surface">Lays Chips Classic</h4>
<span class="text-status-warning font-label-bold text-[10px] uppercase">Review Required</span>
</div>
<div class="flex items-center gap-3">
<select class="bg-surface-container-low border-none rounded-lg py-1.5 px-3 font-bold text-sm focus:ring-0">
<option>1 Qty</option>
<option>2 Qty</option>
</select>
<button class="p-2 text-error hover:bg-error/10 rounded-lg transition-colors">
<span class="material-symbols-outlined">delete</span>
</button>
</div>
</div>
<div class="pt-4 space-y-4">
<h3 class="font-label-bold text-label-bold text-secondary uppercase tracking-[0.2em] px-2">Weighted Item</h3>
<!-- Card: Banana -->
<div class="bg-primary-container/5 border-2 border-primary-container px-panel-padding py-4 rounded-xl shadow-sm flex items-center justify-between">
<div class="flex flex-col">
<h4 class="font-headline-md text-primary-container">Banana</h4>
<div class="flex items-center gap-2 text-sm text-on-surface font-semibold">
<span>1.35 kg</span>
<span class="text-outline">|</span>
<span>128.25 ETB</span>
</div>
</div>
<div class="flex items-center gap-3">
<button class="bg-primary text-on-primary px-4 py-2 rounded-lg font-label-bold text-label-bold hover:brightness-110 transition-all">
                                Add
                            </button>
<button class="p-2 text-error hover:bg-error/10 rounded-lg transition-colors">
<span class="material-symbols-outlined">close</span>
</button>
</div>
</div>
</div>
</div>
<!-- Quick Access Search -->
<div class="mt-auto pt-6 space-y-3">
<div class="flex gap-2">
<div class="relative flex-1">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">barcode_scanner</span>
<input class="w-full pl-10 pr-4 py-2.5 border border-outline-variant rounded-xl font-body-sm focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white" placeholder="Scan Barcode..." type="text"/>
</div>
<button class="bg-primary text-on-primary px-6 rounded-xl font-label-bold text-label-bold">Add</button>
</div>
<div class="flex gap-2">
<div class="relative flex-1">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
<input class="w-full pl-10 pr-4 py-2.5 border border-outline-variant rounded-xl font-body-sm focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white" placeholder="Manual Item Search..." type="text"/>
</div>
<button class="bg-secondary-container text-on-secondary-container px-4 rounded-xl font-label-bold text-label-bold whitespace-nowrap">Find Item</button>
</div>
</div>
</section>
<!-- Right Column: Receipt (Compact) -->
<section class="col-span-12 md:col-span-3 flex flex-col gap-stack-gap h-full">
<div class="bg-panel-bg rounded-xl shadow-sm border border-outline-variant flex flex-col flex-1 overflow-hidden">
<div class="bg-surface-container-low px-4 py-3 border-b border-outline-variant flex justify-between items-center">
<h2 class="font-headline-md text-on-surface text-sm">Receipt Preview</h2>
<span class="text-status-warning text-[10px] font-bold uppercase">Pending</span>
</div>
<div class="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-3">
<div class="flex justify-between items-start text-sm">
<div class="flex flex-col">
<span class="font-semibold">Fresh Tomatoes</span>
<span class="text-[11px] text-on-surface-variant">0.85kg @ 45.00</span>
</div>
<span class="font-bold">38.25</span>
</div>
<div class="flex justify-between items-start text-sm">
<div class="flex flex-col">
<span class="font-semibold">Milk 1L</span>
<span class="text-[11px] text-on-surface-variant">2 x 55.00</span>
</div>
<span class="font-bold">110.00</span>
</div>
<div class="flex justify-between items-start text-sm">
<div class="flex flex-col">
<span class="font-semibold">Wheat Bread</span>
<span class="text-[11px] text-on-surface-variant">1 x 65.00</span>
</div>
<span class="font-bold">65.00</span>
</div>
</div>
<div class="bg-surface-container-lowest p-4 border-t border-dashed border-outline-variant">
<div class="flex justify-between items-center text-xs text-on-surface-variant mb-1">
<span>VAT (15%)</span>
<span>40.00</span>
</div>
<div class="flex justify-between items-center mt-2">
<span class="font-black text-xs uppercase">Total</span>
<span class="text-headline-md font-black text-primary">278.25 ETB</span>
</div>
</div>
</div>
<div class="bg-panel-bg p-4 rounded-xl shadow-sm border border-outline-variant space-y-4">
<select class="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2.5 px-3 text-sm font-semibold focus:ring-primary">
<option>Cash Payment</option>
<option>Mobile Money</option>
<option>Card Payment</option>
</select>
<button class="w-full bg-primary text-on-primary py-4 rounded-xl font-label-bold text-label-bold shadow-lg hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2">
                    Complete Transaction
                    <span class="material-symbols-outlined">chevron_right</span>
</button>
</div>
</section>
</main>
<footer class="fixed bottom-0 left-0 right-0 h-1.5 bg-primary/20"></footer>
</body></html>
