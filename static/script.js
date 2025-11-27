const form = document.getElementById('generate-form');
const statusIndicator = document.getElementById('status-indicator');
const treeContainer = document.getElementById('tree-container');

let ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onopen = () => {
    console.log("Connected to WebSocket");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received data:", data);
    handleMessage(data);
};

ws.onclose = () => {
    console.log("Disconnected from WebSocket");
    statusIndicator.textContent = "DISCONNECTED";
    statusIndicator.classList.remove('generating');
};

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const role = document.getElementById('role').value;
    const query = document.getElementById('query').value;
    const mode = document.getElementById('mode').value;

    // Clear previous tree
    treeContainer.innerHTML = '';
    statusIndicator.textContent = "GENERATING...";
    statusIndicator.classList.add('generating');

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role, query, mode })
        });

        if (!response.ok) {
            throw new Error('Failed to start generation');
        }

    } catch (error) {
        console.error(error);
        statusIndicator.textContent = "ERROR";
        statusIndicator.classList.remove('generating');
        alert("Error starting generation: " + error.message);
    }
});

function handleMessage(data) {
    if (data.type === 'root') {
        renderRoot(data.node);
    } else if (data.type === 'expand') {
        renderExpansion(data.parent_answer_id, data.node);
    } else if (data.type === 'complete') {
        statusIndicator.textContent = "COMPLETE";
        statusIndicator.classList.remove('generating');
    } else if (data.type === 'error') {
        statusIndicator.textContent = "ERROR";
        statusIndicator.classList.remove('generating');
        alert("Error: " + data.message);
    }
}

function createQuestionElement(node) {
    const div = document.createElement('div');
    div.className = 'question-node';
    div.id = `question-${node.id}`;

    const text = document.createElement('div');
    text.className = 'question-text';
    text.textContent = `Q: ${node.question}`;
    div.appendChild(text);

    const answersContainer = document.createElement('div');
    answersContainer.className = 'answers-container';

    node.answers.forEach(ans => {
        const ansDiv = document.createElement('div');
        ansDiv.className = 'answer-node';
        ansDiv.id = `answer-${ans.id}`;

        // Add click handler for interactive mode
        ansDiv.onclick = (e) => {
            e.stopPropagation();
            handleAnswerClick(ans.id);
        };
        ansDiv.style.cursor = 'pointer';
        ansDiv.title = 'Click to expand';

        const ansText = document.createElement('div');
        ansText.className = 'answer-text';
        ansText.textContent = ans.text;
        ansDiv.appendChild(ansText);

        const outcomes = document.createElement('div');
        outcomes.className = 'outcomes';
        outcomes.textContent = `Outcomes: ${ans.outcomes.join(', ')}`;
        ansDiv.appendChild(outcomes);

        const childContainer = document.createElement('div');
        childContainer.className = 'child-container';
        childContainer.id = `child-container-${ans.id}`;
        ansDiv.appendChild(childContainer);

        answersContainer.appendChild(ansDiv);
    });

    div.appendChild(answersContainer);
    return div;
}

function renderRoot(node) {
    treeContainer.innerHTML = ''; // Ensure clear
    const el = createQuestionElement(node);
    treeContainer.appendChild(el);
}

function renderExpansion(parentAnswerId, node) {
    const container = document.getElementById(`child-container-${parentAnswerId}`);
    if (container) {
        const el = createQuestionElement(node);
        container.appendChild(el);

        // Scroll to view
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error(`Parent answer container ${parentAnswerId} not found`);
    }
}

async function handleAnswerClick(answerId) {
    const mode = document.getElementById('mode').value;
    if (mode !== 'interactive') return;

    // Check if already expanded
    const container = document.getElementById(`child-container-${answerId}`);
    if (container && container.children.length > 0) return;

    statusIndicator.textContent = "EXPANDING...";
    statusIndicator.classList.add('generating');

    const role = document.getElementById('role').value;
    const query = document.getElementById('query').value;

    try {
        const response = await fetch('/expand', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ role, query, answer_id: answerId })
        });

        if (!response.ok) {
            throw new Error('Failed to expand node');
        }
    } catch (error) {
        console.error(error);
        statusIndicator.textContent = "ERROR";
        statusIndicator.classList.remove('generating');
        alert("Error expanding node: " + error.message);
    }
}
