import os
import json
import re
import csv
import numpy as np
from scipy.stats import pearsonr

# Paths
json_dir = ''
annotations_path = ''

# Read the averaged annotations CSV
annotations = {}
with open(annotations_path, 'r', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        audio_file = row['audio']
        annotations[audio_file] = {
            'accuracy_avg': float(row['accuracy_avg']),
            'fluency_avg': float(row['fluency_avg']),
            'prosody_avg': float(row['prosody_avg'])
        }
print(f"Loaded {len(annotations)} entries from annotations file")

# Extract scores from all JSON files
json_scores = {}
missing_files = []

for filename in os.listdir(json_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(json_dir, filename)
        try:
            with open(filepath, 'r') as f:
                json_content = json.load(f)
            
            # Extract the JSON string from the response field
            match = re.search(r'```json\n(.*?)\n```', json_content['response'], re.DOTALL)
            if match:
                inner_json_str = match.group(1)
                inner_json = json.loads(inner_json_str)
                
                accuracy = inner_json.get('Accuracy', {}).get('score', None)
                fluency = inner_json.get('Fluency', {}).get('score', None)
                prosody = inner_json.get('Prosody', {}).get('score', None)
                
                if accuracy is not None and fluency is not None and prosody is not None:
                    json_scores[filename] = {
                        'accuracy': accuracy,
                        'fluency': fluency,
                        'prosody': prosody
                    }
                else:
                    missing_files.append(filename)
            else:
                print(f"Could not extract inner JSON from {filename}")
                missing_files.append(filename)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            missing_files.append(filename)

print(f"Successfully extracted scores from {len(json_scores)} files")
if missing_files:
    print(f"{len(missing_files)} files had issues.")

# Match JSON files with annotation files
matched_pairs = []

for audio_file, anno_scores in annotations.items():
    # Remove .wav extension to match JSON filenames
    base_name = audio_file.replace('.wav', '')
    json_file = base_name + '.json'
    
    if json_file in json_scores:
        matched_pairs.append({
            'audio': audio_file,
            'json_accuracy': json_scores[json_file]['accuracy'],
            'json_fluency': json_scores[json_file]['fluency'],
            'json_prosody': json_scores[json_file]['prosody'],
            'annotation_accuracy': anno_scores['accuracy_avg'],
            'annotation_fluency': anno_scores['fluency_avg'],
            'annotation_prosody': anno_scores['prosody_avg']
        })

print(f"Matched {len(matched_pairs)} files between JSON and annotations")

if matched_pairs:
    # Extract scores for correlation calculation
    json_accuracy = np.array([item['json_accuracy'] for item in matched_pairs])
    json_fluency = np.array([item['json_fluency'] for item in matched_pairs])
    json_prosody = np.array([item['json_prosody'] for item in matched_pairs])
    
    anno_accuracy = np.array([item['annotation_accuracy'] for item in matched_pairs])
    anno_fluency = np.array([item['annotation_fluency'] for item in matched_pairs])
    anno_prosody = np.array([item['annotation_prosody'] for item in matched_pairs])
    
    # Calculate PCCs using scipy.stats.pearsonr
    accuracy_pcc, accuracy_p = pearsonr(json_accuracy, anno_accuracy)
    fluency_pcc, fluency_p = pearsonr(json_fluency, anno_fluency)
    prosody_pcc, prosody_p = pearsonr(json_prosody, anno_prosody)
    
    print("\nPearson Correlation Coefficient Results:")
    print(f"Accuracy PCC: {accuracy_pcc:.4f} (p-value: {accuracy_p:.4f})")
    print(f"Fluency PCC: {fluency_pcc:.4f} (p-value: {fluency_p:.4f})")
    print(f"Prosody PCC: {prosody_pcc:.4f} (p-value: {prosody_p:.4f})")
else:
    print("No matches found between JSON files and annotations")