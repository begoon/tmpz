class AlertButton extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: "open" });

        const style = document.createElement("style");
        style.textContent = `
      button {
        padding: 0.5em 1em;
        font-size: 1rem;
        cursor: pointer;
      }
    `;

        const button = document.createElement("button");

        const slot = document.createElement("slot");
        button.appendChild(slot);

        shadow.appendChild(style);
        shadow.appendChild(button);

        this.button = button;
    }

    connectedCallback() {
        this.button.addEventListener("click", this.handleClick);
    }

    disconnectedCallback() {
        this.button.removeEventListener("click", this.handleClick);
    }

    handleClick = () => {
        this.dispatchEvent(new CustomEvent("button-click", { bubbles: true, composed: true }));
    };
}

customElements.define("alert-button", AlertButton);
