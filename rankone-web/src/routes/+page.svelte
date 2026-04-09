<script lang="ts">
    let { data } = $props();

    interface Detection {
        x: number;
        y: number;
        width: number;
        height: number;
        confidence: number;
        leftEye?: { x: number; y: number };
        rightEye?: { x: number; y: number };
        nose?: { x: number; y: number };
        rightMouthCorner?: { x: number; y: number };
        leftMouthCorner?: { x: number; y: number };
        chin?: { x: number; y: number };
    }

    interface SlotData {
        src: string;
        type: "face" | "fingerprint" | null;
        template: any;
        detection: Detection | null;
        showDetection: boolean;
        loading: boolean;
        naturalWidth: number;
        naturalHeight: number;
    }

    const gallery = [
        { src: "/i/faces/a1.jpg", name: "Face A1" },
        { src: "/i/faces/a2.jpg", name: "Face A2" },
        { src: "/i/faces/b.jpg", name: "Face B" },
        { src: "/i/faces/c.jpg", name: "Face C" },
        { src: "/i/faces/d.jpg", name: "Face D" },
        { src: "/i/faces/e1.jpg", name: "Face E1" },
        { src: "/i/faces/e2.jpg", name: "Face E2" },
        { src: "/i/faces/e3.jpg", name: "Face E3" },
        { src: "/i/fingerprints/a1.png", name: "FP A1" },
        { src: "/i/fingerprints/a2.png", name: "FP A2" },
    ];

    let slots: [SlotData | null, SlotData | null] = $state([null, null]);
    let similarity: number | null = $state(null);
    let comparing = $state(false);

    function handleDragStart(e: DragEvent, src: string) {
        e.dataTransfer?.setData("text/plain", src);
    }

    function handleDrop(e: DragEvent, index: 0 | 1) {
        e.preventDefault();
        const src = e.dataTransfer?.getData("text/plain");
        if (!src) return;
        similarity = null;
        loadImage(src, index);
    }

    function handleDragOver(e: DragEvent) {
        e.preventDefault();
    }

    function clearSlot(index: 0 | 1) {
        slots[index] = null;
        similarity = null;
    }

    async function loadImage(src: string, index: 0 | 1) {
        const slot: SlotData = {
            src,
            type: null,
            template: null,
            detection: null,
            showDetection: false,
            loading: true,
            naturalWidth: 0,
            naturalHeight: 0,
        };
        slots[index] = slot;

        // Load image to get natural dimensions and base64
        const img = new Image();
        img.crossOrigin = "anonymous";
        await new Promise<void>((resolve) => {
            img.onload = () => resolve();
            img.src = src;
        });
        slot.naturalWidth = img.naturalWidth;
        slot.naturalHeight = img.naturalHeight;

        // Convert to base64
        const canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext("2d")!;
        ctx.drawImage(img, 0, 0);
        const dataUrl = canvas.toDataURL("image/png");
        const base64 = dataUrl.split(",")[1]!;

        // Call both APIs in parallel to detect type
        const [faceResponse, fingerprintResponse] = await Promise.allSettled([
            fetch("/api/represent", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: base64 }),
            }).then((r) => r.json()),
            fetch("/api/represent-fingerprint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: base64 }),
            }).then((r) => r.json()),
        ]);

        const faceTemplate = faceResponse.status === "fulfilled" ? faceResponse.value.template : null;
        const fingerprintTemplate =
            fingerprintResponse.status === "fulfilled" ? fingerprintResponse.value.template : null;

        const faceConf = faceTemplate?.detection?.confidence ?? -Infinity;
        const fingerprintConf = fingerprintTemplate?.detection?.confidence ?? -Infinity;

        if (faceConf > fingerprintConf && faceTemplate) {
            slot.type = "face";
            slot.template = faceTemplate;
            slot.detection = faceTemplate.detection;
        } else if (fingerprintTemplate) {
            slot.type = "fingerprint";
            slot.template = fingerprintTemplate;
            slot.detection = fingerprintTemplate.detection;
        }

        slot.showDetection = true;
        slot.loading = false;
        slots[index] = slot;
        requestAnimationFrame(() => redrawCanvas(index));

        // Auto-compare if both slots loaded with same type
        const other = slots[index === 0 ? 1 : 0];
        if (other && !other.loading && slot.type && slot.type === other.type) {
            compare();
        }
    }

    async function compare() {
        if (!slots[0]?.template || !slots[1]?.template || !slots[0]?.type) return;
        comparing = true;
        similarity = null;
        try {
            const res = await fetch("/api/compare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    type: slots[0].type,
                    a: slots[0].template,
                    b: slots[1].template,
                }),
            });
            const data = await res.json();
            similarity = data.similarity;
        } finally {
            comparing = false;
        }
    }

    function drawDetections(canvas: HTMLCanvasElement, slot: SlotData) {
        const ctx = canvas.getContext("2d");
        if (!ctx || !slot.detection) return;

        const det = slot.detection;
        const displayWidth = canvas.width;
        const displayHeight = canvas.height;
        const scaleX = displayWidth / slot.naturalWidth;
        const scaleY = displayHeight / slot.naturalHeight;

        ctx.clearRect(0, 0, displayWidth, displayHeight);

        // Draw bounding box
        const cx = det.x * scaleX;
        const cy = det.y * scaleY;
        const w = det.width * scaleX;
        const h = det.height * scaleY;
        const x0 = cx - w / 2;
        const y0 = cy - h / 2;

        ctx.strokeStyle = "lightskyblue";
        ctx.lineWidth = 2;
        ctx.strokeRect(x0, y0, w, h);

        // Draw keypoints for faces
        if (slot.type === "face") {
            const keypoints = ["leftEye", "rightEye", "nose", "rightMouthCorner", "leftMouthCorner", "chin"] as const;
            const r = 5;
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            for (const kp of keypoints) {
                const point = det[kp];
                if (point) {
                    const px = point.x * scaleX;
                    const py = point.y * scaleY;
                    ctx.beginPath();
                    ctx.moveTo(px - r, py - r);
                    ctx.lineTo(px + r, py + r);
                    ctx.stroke();
                    ctx.beginPath();
                    ctx.moveTo(px - r, py + r);
                    ctx.lineTo(px + r, py - r);
                    ctx.stroke();
                }
            }
        }
    }

    let canvasEls: [HTMLCanvasElement | null, HTMLCanvasElement | null] = $state([null, null]);

    function redrawCanvas(idx: 0 | 1) {
        const canvas = canvasEls[idx];
        const slot = slots[idx];
        if (!canvas) return;
        if (slot && !slot.loading && slot.detection && slot.showDetection) {
            const container = canvas.parentElement!;
            const img = container.querySelector("img");
            if (img && img.clientWidth > 0) {
                canvas.width = img.clientWidth;
                canvas.height = img.clientHeight;
                drawDetections(canvas, slot);
                return;
            }
        }
        const ctx = canvas.getContext("2d");
        if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
</script>

<svelte:head>
    <title>Rankone Web</title>
</svelte:head>

<div class="app">
    <h1>Rankone Biometrics</h1>
    <p class="versions">Face: {data.versions.face} | Fingerprint: {data.versions.fingerprint}</p>

    <div class="placeholders">
        {#each [0, 1] as idx}
            {@const slot = slots[idx as 0 | 1]}
            <div class="slot-column">
                <div
                    class="placeholder"
                    ondragover={handleDragOver}
                    ondrop={(e) => handleDrop(e, idx as 0 | 1)}
                    ondblclick={() => clearSlot(idx as 0 | 1)}
                    role="img"
                    aria-label="Image slot {idx + 1}"
                >
                    {#if slot}
                        <div class="image-container">
                            {#if slot.type}
                                <span class="type-label">{slot.type}</span>
                            {/if}
                            <img
                                src={slot.src}
                                alt="Slot {idx + 1}"
                                onload={() => {
                                    slots[idx as 0 | 1] = slot;
                                }}
                            />
                            <canvas bind:this={canvasEls[idx as 0 | 1]}></canvas>
                            {#if slot.loading}
                                <div class="loading-overlay">detecting...</div>
                            {/if}
                        </div>
                    {:else}
                        <div class="empty">
                            <span>Drop image here</span>
                        </div>
                    {/if}
                </div>
                {#if slot?.detection}
                    <div class="confidence">confidence = {slot.detection.confidence.toFixed(4)}</div>
                {/if}
            </div>
        {/each}
    </div>

    {#if similarity !== null}
        <div class="similarity">
            similarity = {similarity.toFixed(4)}
        </div>
    {/if}

    {#if comparing}
        <div class="similarity">comparing...</div>
    {/if}

    <div class="gallery">
        <h2>Gallery</h2>
        <div class="gallery-grid">
            {#each gallery as item}
                <div
                    class="gallery-item"
                    draggable="true"
                    ondragstart={(e) => handleDragStart(e, item.src)}
                    role="img"
                    aria-label={item.name}
                >
                    <img src={item.src} alt={item.name} draggable="false" />
                    <span>{item.name}</span>
                </div>
            {/each}
        </div>
    </div>
</div>

<style>
    :global(body) {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #1a1a2e;
        color: #e0e0e0;
    }

    .app {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }

    h1 {
        text-align: center;
        color: lightskyblue;
        margin-bottom: 4px;
    }

    .versions {
        text-align: center;
        color: #666;
        font-size: 12px;
        font-family: monospace;
        margin: 0 0 24px;
    }

    h2 {
        color: #aaa;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }

    .placeholders {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 16px;
    }

    .slot-column {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .placeholder {
        width: 420px;
        min-height: 320px;
        border: 2px dashed #444;
        border-radius: 8px;
        overflow: hidden;
        background: #16213e;
        cursor: default;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .placeholder:hover {
        border-color: #666;
    }

    .image-container {
        position: relative;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .image-container img {
        max-width: 100%;
        max-height: 400px;
        display: block;
    }

    .image-container canvas {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
    }

    .type-label {
        position: absolute;
        top: 8px;
        left: 8px;
        background: rgba(135, 206, 250, 0.85);
        color: #1a1a2e;
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 3px 10px;
        border-radius: 4px;
        z-index: 2;
    }

    .loading-overlay {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: lightskyblue;
        font-size: 18px;
        z-index: 3;
    }

    .confidence {
        text-align: center;
        font-family: monospace;
        font-size: 13px;
        color: lightskyblue;
        padding: 6px 0 0;
    }

    .empty {
        color: #555;
        font-size: 14px;
        text-align: center;
        padding: 40px;
    }

    .similarity {
        text-align: center;
        font-size: 22px;
        font-family: monospace;
        color: lightskyblue;
        margin-bottom: 16px;
    }

    .gallery-grid {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }

    .gallery-item {
        cursor: grab;
        border: 2px solid #333;
        border-radius: 6px;
        overflow: hidden;
        background: #16213e;
        text-align: center;
        transition: border-color 0.2s;
    }

    .gallery-item:hover {
        border-color: lightskyblue;
    }

    .gallery-item img {
        width: 120px;
        height: 100px;
        object-fit: cover;
        display: block;
    }

    .gallery-item span {
        display: block;
        font-size: 11px;
        padding: 4px;
        color: #aaa;
    }
</style>
