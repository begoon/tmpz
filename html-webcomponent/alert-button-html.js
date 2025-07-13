class AlertButton extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });

        this.shadowRoot.innerHTML = `
      <style>
        button {
          padding: 0.5em 1em;
          font-size: 1rem;
          cursor: pointer;
        }
      </style>
      <button><slot></slot></button>
    `;
    }

    connectedCallback() {
        this.shadowRoot.querySelector("button").addEventListener("click", () => {
            alert("Button clicked!");
        });
    }

    disconnectedCallback() {
        this.shadowRoot.querySelector("button").removeEventListener("click");
    }
}

customElements.define("alert-button", AlertButton);
