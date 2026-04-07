import { RANKONE_250, RANKONE_330 } from "$env/static/private";

async function rpc(url: string, request: Record<string, unknown>): Promise<Record<string, unknown>> {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        throw new Error(`RPC error: ${response.status} ${await response.text()}`);
    }
    return response.json();
}

export async function representFace(imageBase64: string) {
    const response = await rpc(RANKONE_330, {
        represent: {
            image: imageBase64,
            algorithmOptions: ["ROC_FACE_DETECTION", "ROC_FACE_BALANCED_REPRESENTATION"],
            minQuality: -4.0,
            minSize: 20,
            falseDetectionRate: 0.02,
            k: 1,
        },
    });
    const represent = response.represent as { templates: Record<string, unknown>[] } | null;
    if (!represent?.templates?.length) return null;
    return represent.templates[0];
}

export async function representFingerprint(imageBase64: string) {
    const response = await rpc(RANKONE_250, {
        representFingerprint: {
            image: imageBase64,
            fingerOptions: ["ROC_UNKNOWN_FINGER"],
            resolution: 500,
            k: 1,
            falseDetectionRate: 0.5,
            minQuality: -3.4028234663852886e38,
        },
    });
    const represent = response.representFingerprint as { templates: Record<string, unknown>[] } | null;
    if (!represent?.templates?.length) return null;
    return represent.templates[0];
}

export async function versionStrings(): Promise<{ face: string; fingerprint: string }> {
    const [faceResponse, fingerprintResponse] = await Promise.all([
        rpc(RANKONE_330, { versionString: {} }),
        rpc(RANKONE_250, { versionString: {} }),
    ]);
    return {
        face: (faceResponse.versionString as any).version as string,
        fingerprint: (fingerprintResponse.versionString as any).version as string,
    };
}

export async function compareTemplates(
    type: "face" | "fingerprint",
    a: Record<string, unknown>,
    b: Record<string, unknown>,
): Promise<number> {
    const url = type === "face" ? RANKONE_330 : RANKONE_250;
    const response = await rpc(url, { compareTemplates: { a, b } });
    const cmp = response.compareTemplates as any;
    return cmp.similarity;
}
