<script>
    export let w;
    export let h;
    export let c;
    export let color = undefined;
    export let background = undefined;
</script>

<svg width={w} height={h} style="background-color: {background}">
    <text
        textLength="100%"
        lengthAdjust="spacingAndGlyphs"
        dominant-baseline="hanging"
        transform="scale(0.7, 1.0)"
        font-size={h}
        font-family="Source Code Pro"
        fill={color}
    >
        {c}
    </text>
</svg>

<style>
    @import url("https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap");
</style>
