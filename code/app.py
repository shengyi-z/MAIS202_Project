# -*- coding: utf-8 -*-
"""website

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1R5AH_vfzrKpJvWtaBisfX2HPjJnpOMir
"""

# @title
import torch
from transformers import DistilBertTokenizer, PreTrainedModel, DistilBertConfig, DistilBertModel
import torch.nn as nn
import torch.nn.functional as F
from flask import Flask, request, jsonify
from google.colab.output import eval_js
import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

class CrisisBERTForHub(PreTrainedModel):
    config_class = DistilBertConfig

    def __init__(self, config):
        super().__init__(config)
        self.bert = DistilBertModel(config)
        self.classifier = nn.Linear(config.hidden_size, 9)  # 9 classes

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        return self.classifier(pooled_output)

# Load model globally
print("Loading model...")
tokenizer = DistilBertTokenizer.from_pretrained("liiinn/crisis-bert")
model = CrisisBERTForHub.from_pretrained("liiinn/crisis-bert")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
model.eval()
print("Model loaded!")

def get_predictions(texts, batch_size=32):
    """Helper function to get predictions for multiple texts"""
    all_predictions = []
    all_probabilities = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]

        encodings = tokenizer(
            batch_texts,
            max_length=54,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        ).to(device)

        with torch.no_grad():
            outputs = model(encodings['input_ids'], encodings['attention_mask'])
            probabilities = F.softmax(outputs, dim=1)
            predictions = torch.argmax(outputs, dim=1)

        all_predictions.extend(predictions.cpu().numpy())
        all_probabilities.extend(probabilities.cpu().numpy())

    return all_predictions, all_probabilities

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Crisis Text Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-8 text-center">Crisis Text Analysis</h1>

        <!-- Tabs -->
        <div class="mb-8">
            <button onclick="showTab('single')" class="px-4 py-2 mr-2 bg-blue-500 text-white rounded">Single Tweet</button>
            <button onclick="showTab('bulk')" class="px-4 py-2 bg-blue-500 text-white rounded">Bulk Analysis</button>
        </div>

        <!-- Single Tweet Analysis -->
        <div id="singleTab" class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Single Tweet Analysis</h2>
            <textarea
                id="inputText"
                class="w-full h-32 p-4 border rounded mb-4"
                placeholder="Enter crisis-related text to analyze..."></textarea>

            <button
                onclick="analyzeText()"
                class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">
                Analyze Text
            </button>

            <div id="singleLoading" class="hidden mt-4">
                Analyzing...
            </div>

            <div id="singleResults" class="mt-8">
                <canvas id="resultsChart"></canvas>
            </div>
        </div>

        <!-- Bulk Analysis -->
        <div id="bulkTab" class="hidden bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-bold mb-4">Bulk Tweet Analysis</h2>

            <!-- CSV Upload Instructions -->
            <div class="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 class="font-bold text-blue-800 mb-2">CSV File Requirements:</h3>
                <ul class="list-disc pl-5 text-blue-800">
                    <li>File must be in CSV format</li>
                    <li>Should contain exactly one column named "tweet_text"</li>
                    <li>Each row should contain a single tweet/text to analyze</li>
                    <li>Example CSV format:
                        <pre class="mt-2 bg-white p-2 rounded">tweet_text
"First tweet content here"
"Second tweet content here"
"Third tweet content here"</pre>
                    </li>
                </ul>
            </div>

            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700">Upload CSV file</label>
                <input type="file" id="csvFile" accept=".csv" class="mt-1 block w-full" />
            </div>

            <button
                onclick="analyzeBulk()"
                class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">
                Analyze CSV
            </button>

            <div id="bulkLoading" class="hidden mt-4">
                Analyzing bulk data...
            </div>

            <div id="bulkResults" class="mt-8">
                <div id="statsContainer"></div>
                <canvas id="pieChart" class="mb-8"></canvas>
                <canvas id="barChart" class="mb-8"></canvas>

                <!-- Classified Tweets Section -->
                <div id="classifiedTweets" class="mt-8">
                    <h3 class="text-xl font-bold mb-4">Classified Tweets</h3>
                    <div id="tweetsByCategory"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let resultsChart = null;
        let pieChart = null;
        let barChart = null;

        function showTab(tabName) {
            document.getElementById('singleTab').classList.add('hidden');
            document.getElementById('bulkTab').classList.add('hidden');

            if (tabName === 'single') {
                document.getElementById('singleTab').classList.remove('hidden');
            } else {
                document.getElementById('bulkTab').classList.remove('hidden');
            }
        }

        async function analyzeText() {
            const text = document.getElementById('inputText').value;
            if (!text) {
                alert('Please enter some text to analyze');
                return;
            }

            document.getElementById('singleLoading').classList.remove('hidden');

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text })
                });

                const results = await response.json();

                if (resultsChart) {
                    resultsChart.destroy();
                }

                const ctx = document.getElementById('resultsChart').getContext('2d');
                resultsChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: results.map(r => r.label),
                        datasets: [{
                            label: 'Probability',
                            data: results.map(r => r.probability),
                            backgroundColor: 'rgba(59, 130, 246, 0.5)'
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            x: {
                                beginAtZero: true,
                                max: 1
                            }
                        }
                    }
                });

            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while analyzing the text');
            } finally {
                document.getElementById('singleLoading').classList.add('hidden');
            }
        }

        async function analyzeBulk() {
            const fileInput = document.getElementById('csvFile');
            const file = fileInput.files[0];

            if (!file) {
                alert('Please select a CSV file');
                return;
            }

            document.getElementById('bulkLoading').classList.remove('hidden');

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/analyze_bulk', {
                    method: 'POST',
                    body: formData
                });

                const results = await response.json();

                // Display statistics
                document.getElementById('statsContainer').innerHTML = `
                    <div class="mb-8 p-4 bg-gray-50 rounded">
                        <h3 class="font-bold mb-2">Summary Statistics</h3>
                        <p>Total tweets analyzed: ${results.total_tweets}</p>
                        <p>Average confidence: ${results.avg_confidence.toFixed(3)}</p>
                        <p>Median confidence: ${results.median_confidence.toFixed(3)}</p>
                    </div>
                `;

                // Update charts
                if (pieChart) pieChart.destroy();
                if (barChart) barChart.destroy();

                // Pie Chart
                const pieCtx = document.getElementById('pieChart').getContext('2d');
                pieChart = new Chart(pieCtx, {
                    type: 'pie',
                    data: {
                        labels: Object.keys(results.label_counts),
                        datasets: [{
                            data: Object.values(results.label_counts),
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                                '#FF9F40', '#FF6384', '#36A2EB', '#FFCE56'
                            ]
                        }]
                    }
                });

                // Bar Chart
                const barCtx = document.getElementById('barChart').getContext('2d');
                barChart = new Chart(barCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(results.label_counts),
                        datasets: [{
                            label: 'Number of Tweets',
                            data: Object.values(results.label_counts),
                            backgroundColor: 'rgba(59, 130, 246, 0.5)'
                        }]
                    },
                    options: {
                        indexAxis: 'y'
                    }
                });

                // Display classified tweets
                const tweetsContainer = document.getElementById('tweetsByCategory');
                tweetsContainer.innerHTML = '';

                Object.entries(results.tweets_by_category).forEach(([category, tweets]) => {
                    const categoryDiv = document.createElement('div');
                    categoryDiv.className = 'mb-8';
                    categoryDiv.innerHTML = `
                        <h4 class="font-bold text-lg mb-2 bg-gray-100 p-2 rounded">${category} (${tweets.length} tweets)</h4>
                        <div class="space-y-2">
                            ${tweets.map(tweet => `
                                <div class="p-3 border rounded hover:bg-gray-50">
                                    <p class="text-gray-800">${tweet.text}</p>
                                    <p class="text-sm text-gray-500 mt-1">Confidence: ${tweet.confidence.toFixed(3)}</p>
                                </div>
                            `).join('')}
                        </div>
                    `;
                    tweetsContainer.appendChild(categoryDiv);
                });

            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while analyzing the CSV file');
            } finally {
                document.getElementById('bulkLoading').classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_TEMPLATE

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json['text']

    encoding = tokenizer(
        text,
        max_length=54,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )

    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask)
        probabilities = F.softmax(outputs, dim=1)

    probs = probabilities.cpu().numpy()[0]

    labels = {
        0: "caution_and_advice",
        1: "displaced_people_and_evacuations",
        2: "donation_needs_or_offers_or_volunteering_services",
        3: "infrastructure_and_utilities_damage",
        4: "injured_or_dead_people",
        5: "missing_trapped_or_found_people",
        6: "not_related_or_irrelevant",
        7: "other_useful_information",
        8: "sympathy_and_emotional_support"
    }

    results = [{"label": labels[i], "probability": float(prob)}
               for i, prob in enumerate(probs)]
    results.sort(key=lambda x: x['probability'], reverse=True)

    return jsonify(results)

@app.route('/analyze_bulk', methods=['POST'])
def analyze_bulk():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Read CSV
        df = pd.read_csv(file)
        if 'tweet_text' not in df.columns:
            return jsonify({'error': 'CSV must contain a "tweet_text" column'}), 400

        texts = df['tweet_text'].tolist()

        # Get predictions
        predictions, probabilities = get_predictions(texts)

        # Convert to labels
        label_mapping = {
            0: "caution_and_advice",
            1: "displaced_people_and_evacuations",
            2: "donation_needs_or_offers_or_volunteering_services",
            3: "infrastructure_and_utilities_damage",
            4: "injured_or_dead_people",
            5: "missing_trapped_or_found_people",
            6: "not_related_or_irrelevant",
            7: "other_useful_information",
            8: "sympathy_and_emotional_support"
        }

        predicted_labels = [label_mapping[pred] for pred in predictions]
        confidence_scores = [max(probs) for probs in probabilities]

        # Organize tweets by category
        tweets_by_category = {}
        for text, label, confidence in zip(texts, predicted_labels, confidence_scores):
            if label not in tweets_by_category:
                tweets_by_category[label] = []
            tweets_by_category[label].append({
                'text': text,
                'confidence': float(confidence)
            })

        # Sort tweets within each category by confidence
        for category in tweets_by_category:
            tweets_by_category[category].sort(key=lambda x: x['confidence'], reverse=True)

        # Compute statistics
        label_counts = pd.Series(predicted_labels).value_counts().to_dict()

        results = {
            'total_tweets': len(texts),
            'label_counts': label_counts,
            'avg_confidence': float(np.mean(confidence_scores)),
            'median_confidence': float(np.median(confidence_scores)),
            'tweets_by_category': tweets_by_category
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

print(eval_js("google.colab.kernel.proxyPort(5000)"))
app.run(host='0.0.0.0', port=5000)