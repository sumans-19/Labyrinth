import { getBackendHttpBase } from './runtime';

export class KeystrokeCapture {

    constructor(sessionId, userId, onScoreUpdate) {
        this.sessionId = sessionId;
        this.userId = userId;
        this.onScoreUpdate = onScoreUpdate;
        this.keyDownTimes = {};
        this.lastKeyUp = null;
        this.currentCommand = [];
        this.attachedElement = null;
    }

    attach(inputElement) {
        if (this.attachedElement) {
            this.detach();
        }
        this.attachedElement = inputElement;
        this._keyDownHandler = this._onKeyDown.bind(this);
        this._keyUpHandler = this._onKeyUp.bind(this);
        
        inputElement.addEventListener('keydown', this._keyDownHandler);
        inputElement.addEventListener('keyup', this._keyUpHandler);
    }

    detach() {
        if (this.attachedElement) {
            this.attachedElement.removeEventListener('keydown', this._keyDownHandler);
            this.attachedElement.removeEventListener('keyup', this._keyUpHandler);
            this.attachedElement = null;
        }
    }

    _onKeyDown(e) {
        if (!this.keyDownTimes[e.code]) {
            this.keyDownTimes[e.code] = performance.now();
        }
        if (e.code === 'Enter') {
            // Read value before React clears it on submit
            this.lastCapturedCommand = this.attachedElement ? this.attachedElement.value : '';
        }
    }

    _onKeyUp(e) {
        const pressTime = this.keyDownTimes[e.code] || performance.now();
        const dwell = performance.now() - pressTime;
        const flight = this.lastKeyUp ? performance.now() - this.lastKeyUp : 0;
        
        this.lastKeyUp = performance.now();
        delete this.keyDownTimes[e.code]; // reset
        
        this.currentCommand.push({ key: e.code, dwell, flight });

        if (e.code === 'Enter') {
            this._submitCommand();
        }
    }

    async _submitCommand() {
        if (this.currentCommand.length === 0) return;
        
        const rawCommand = this.lastCapturedCommand || '';
        const payload = { keystrokes: [...this.currentCommand], raw_command: rawCommand };
        this.currentCommand = [];
        this.lastCapturedCommand = '';
        
        try {
            const response = await fetch(`${getBackendHttpBase()}/api/impersonator/event`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    user_id: this.userId,
                    event_type: 'keystroke',
                    timestamp: Date.now(),
                    payload: payload
                })
            });
            const data = await response.json();
            if (this.onScoreUpdate) {
                this.onScoreUpdate(data);
            }
        } catch (e) {
            console.error("Impersonator tracking error:", e);
        }
    }
}
