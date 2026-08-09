"""
Multi-dataset data pipeline for TrueSender.
Combines Enron, SpamAssassin, Kaggle phishing, and SMS (ablation only) datasets.
Handles normalization, deduplication, class imbalance, and domain shift analysis.
"""

import os
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataPipeline:
    """Pipeline to load, process, and combine multiple email datasets."""
    
    def __init__(self, raw_data_dir: str, processed_data_dir: str):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard schema
        self.COLUMNS = ['text', 'label', 'source_dataset']
        
    def load_enron_dataset(self) -> pd.DataFrame:
        """
        Load Enron-Spam Corpus.
        Expected structure: data/raw/enron/ with spam and ham folders,
        or a single enron_spam_data.csv file.
        """
        enron_path = self.raw_data_dir / 'enron'
        if not enron_path.exists():
            logger.warning(f"Enron dataset not found at {enron_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        # Check for CSV first (much faster)
        csv_file = enron_path / 'enron_spam_data.csv'
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file, on_bad_lines='skip')
                
                texts = []
                labels = []
                
                # Try to find message and label columns
                msg_col = 'Message' if 'Message' in df.columns else 'text' if 'text' in df.columns else None
                label_col = 'Spam/Ham' if 'Spam/Ham' in df.columns else 'label' if 'label' in df.columns else None
                
                if msg_col and label_col:
                    texts = df[msg_col].fillna('').astype(str).tolist()
                    for val in df[label_col]:
                        val_str = str(val).lower()
                        labels.append(1 if 'spam' in val_str else 0)
                    
                    result_df = pd.DataFrame({
                        'text': texts,
                        'label': labels,
                        'source_dataset': 'enron'
                    })
                    logger.info(f"Loaded {len(result_df)} emails from Enron dataset CSV")
                    return result_df
            except Exception as e:
                logger.error(f"Error loading Enron CSV: {e}")
        
        emails = []
        
        # Load spam emails
        spam_dir = enron_path / 'spam'
        if spam_dir.exists():
            for file_path in spam_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        emails.append({'text': text, 'label': 1, 'source_dataset': 'enron'})
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        # Load ham emails
        ham_dir = enron_path / 'ham'
        if ham_dir.exists():
            for file_path in ham_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        emails.append({'text': text, 'label': 0, 'source_dataset': 'enron'})
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        df = pd.DataFrame(emails)
        logger.info(f"Loaded {len(df)} emails from Enron dataset (files)")
        return df
    
    def load_spamassassin_dataset(self) -> pd.DataFrame:
        """
        Load SpamAssassin Public Corpus.
        Expected structure: data/raw/spamassassin/ with spam and ham folders.
        Each file is a single email.
        """
        sa_path = self.raw_data_dir / 'spamassassin'
        if not sa_path.exists():
            logger.warning(f"SpamAssassin dataset not found at {sa_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        emails = []
        
        # Load spam emails
        spam_dir = sa_path / 'spam'
        if spam_dir.exists():
            for file_path in spam_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        emails.append({'text': text, 'label': 1, 'source_dataset': 'spamassassin'})
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        # Load ham emails (easy_ham)
        ham_dir = sa_path / 'easy_ham'
        if ham_dir.exists():
            for file_path in ham_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        emails.append({'text': text, 'label': 0, 'source_dataset': 'spamassassin'})
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        df = pd.DataFrame(emails)
        logger.info(f"Loaded {len(df)} emails from SpamAssassin dataset")
        return df
    
    def load_kaggle_phishing_dataset(self) -> pd.DataFrame:
        """
        Load Kaggle Phishing Email Dataset.
        Expected structure: data/raw/kaggle_phishing/ with a CSV file.
        CSV should have columns like 'Email Text' and 'Email Type'.
        """
        kaggle_path = self.raw_data_dir / 'kaggle_phishing'
        if not kaggle_path.exists():
            logger.warning(f"Kaggle phishing dataset not found at {kaggle_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        # Look for CSV file
        csv_files = list(kaggle_path.glob('*.csv'))
        if not csv_files:
            logger.warning(f"No CSV file found in {kaggle_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        csv_file = csv_files[0]
        try:
            df = pd.read_csv(csv_file)
            
            # Normalize column names (handle different naming conventions)
            # Common column names: 'Email Text', 'Email Type', 'text', 'label', etc.
            text_col = None
            label_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if ('text' in col_lower or 'email' in col_lower) and 'type' not in col_lower:
                    text_col = col
                if 'type' in col_lower or 'label' in col_lower or 'class' in col_lower:
                    label_col = col
            
            if text_col is None or label_col is None:
                logger.warning(f"Could not identify text/label columns in {csv_file}")
                logger.info(f"Available columns: {df.columns.tolist()}")
                return pd.DataFrame(columns=self.COLUMNS)
            
            # Extract text and normalize labels
            texts = df[text_col].fillna('').astype(str)
            
            # Normalize labels: phishing/spam -> 1, safe/ham -> 0
            labels = []
            for val in df[label_col]:
                val_str = str(val).lower()
                if 'phish' in val_str or 'spam' in val_str or 'malicious' in val_str:
                    labels.append(1)
                else:
                    labels.append(0)
            
            result_df = pd.DataFrame({
                'text': texts,
                'label': labels,
                'source_dataset': 'kaggle_phishing'
            })
            
            logger.info(f"Loaded {len(result_df)} emails from Kaggle phishing dataset")
            return result_df
            
        except Exception as e:
            logger.error(f"Error loading Kaggle dataset: {e}")
            return pd.DataFrame(columns=self.COLUMNS)
    
    def load_sms_dataset(self) -> pd.DataFrame:
        """
        Load SMS Spam Collection (UCI) - FOR ABLATION TEST ONLY.
        Expected structure: data/raw/sms/SMSSpamCollection
        Tab-separated format: label\tmessage
        """
        sms_path = self.raw_data_dir / 'sms'
        if not sms_path.exists():
            logger.warning(f"SMS dataset not found at {sms_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        sms_file = sms_path / 'SMSSpamCollection'
        if not sms_file.exists():
            logger.warning(f"SMSSpamCollection file not found at {sms_file}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        try:
            emails = []
            with open(sms_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split('\t', 1)
                    if len(parts) == 2:
                        label_str, text = parts
                        label = 1 if label_str.lower() == 'spam' else 0
                        emails.append({
                            'text': text,
                            'label': label,
                            'source_dataset': 'sms_ablation'
                        })
            
            df = pd.DataFrame(emails)
            logger.info(f"Loaded {len(df)} messages from SMS dataset (ABLATION ONLY)")
            return df
            
        except Exception as e:
            logger.error(f"Error loading SMS dataset: {e}")
            return pd.DataFrame(columns=self.COLUMNS)
    
    def compute_text_hash(self, text: str) -> str:
        """Compute SHA256 hash of text for deduplication."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate and near-duplicate emails using hash-based deduplication.
        """
        if len(df) == 0:
            return df
        
        df = df.copy()
        df['text_hash'] = df['text'].apply(self.compute_text_hash)
        
        initial_count = len(df)
        df = df.drop_duplicates(subset=['text_hash'], keep='first')
        df = df.drop(columns=['text_hash'])
        
        removed = initial_count - len(df)
        logger.info(f"Removed {removed} duplicate emails ({removed/initial_count*100:.2f}%)")
        
        return df
    
    def normalize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Basic text normalization: lowercase, strip whitespace.
        More aggressive cleaning happens in the ML pipeline.
        """
        df = df.copy()
        df['text'] = df['text'].str.lower().str.strip()
        return df
    
    def report_class_balance(self, df: pd.DataFrame, dataset_name: str) -> Dict:
        """Report class balance statistics for a dataset."""
        if len(df) == 0:
            return {}
        
        total = len(df)
        spam_count = (df['label'] == 1).sum()
        ham_count = (df['label'] == 0).sum()
        
        stats = {
            'dataset': dataset_name,
            'total': total,
            'spam': spam_count,
            'ham': ham_count,
            'spam_pct': spam_count / total * 100 if total > 0 else 0,
            'ham_pct': ham_count / total * 100 if total > 0 else 0,
            'avg_text_length': df['text'].str.len().mean()
        }
        
        return stats
    
    def combine_datasets(self, include_sms: bool = False) -> pd.DataFrame:
        """
        Load and combine all datasets.
        SMS is excluded by default (domain shift risk).
        """
        logger.info("="*60)
        logger.info("Loading datasets...")
        logger.info("="*60)
        
        # Load all datasets
        enron_df = self.load_enron_dataset()
        sa_df = self.load_spamassassin_dataset()
        kaggle_df = self.load_kaggle_phishing_dataset()
        sms_df = self.load_sms_dataset() if include_sms else pd.DataFrame(columns=self.COLUMNS)
        
        # Normalize text
        enron_df = self.normalize_text(enron_df)
        sa_df = self.normalize_text(sa_df)
        kaggle_df = self.normalize_text(kaggle_df)
        sms_df = self.normalize_text(sms_df)
        
        # Report individual dataset statistics
        logger.info("\nIndividual Dataset Statistics:")
        logger.info("-"*60)
        
        all_dfs = [
            ('enron', enron_df),
            ('spamassassin', sa_df),
            ('kaggle_phishing', kaggle_df)
        ]
        
        if include_sms:
            all_dfs.append(('sms_ablation', sms_df))
        
        dataset_stats = []
        for name, df in all_dfs:
            stats = self.report_class_balance(df, name)
            if stats:
                dataset_stats.append(stats)
                logger.info(f"{name}:")
                logger.info(f"  Total: {stats['total']}")
                logger.info(f"  Spam: {stats['spam']} ({stats['spam_pct']:.2f}%)")
                logger.info(f"  Ham: {stats['ham']} ({stats['ham_pct']:.2f}%)")
                logger.info(f"  Avg text length: {stats['avg_text_length']:.2f}")
        
        # Combine datasets (excluding SMS by default)
        combined_df = pd.concat([enron_df, sa_df, kaggle_df], ignore_index=True)
        
        # Deduplicate
        logger.info("\nDeduplicating combined dataset...")
        combined_df = self.deduplicate(combined_df)
        
        # Report combined statistics
        logger.info("\nCombined Dataset Statistics:")
        logger.info("-"*60)
        combined_stats = self.report_class_balance(combined_df, 'combined')
        logger.info(f"Total: {combined_stats['total']}")
        logger.info(f"Spam: {combined_stats['spam']} ({combined_stats['spam_pct']:.2f}%)")
        logger.info(f"Ham: {combined_stats['ham']} ({combined_stats['ham_pct']:.2f}%)")
        logger.info(f"Avg text length: {combined_stats['avg_text_length']:.2f}")
        
        # Check for class imbalance
        if combined_stats['spam_pct'] > 65 or combined_stats['ham_pct'] > 65:
            logger.warning(f"Class imbalance detected! Will use class_weight='balanced' in training.")
        
        # Save combined dataset
        output_path = self.processed_data_dir / 'combined_emails.csv'
        combined_df.to_csv(output_path, index=False)
        logger.info(f"\nCombined dataset saved to {output_path}")
        
        # Save statistics report
        report_path = self.processed_data_dir / 'dataset_report.txt'
        with open(report_path, 'w') as f:
            f.write("TrueSender Dataset Report\n")
            f.write("="*60 + "\n\n")
            
            f.write("Individual Dataset Statistics:\n")
            f.write("-"*60 + "\n")
            for stats in dataset_stats:
                f.write(f"\n{stats['dataset']}:\n")
                f.write(f"  Total: {stats['total']}\n")
                f.write(f"  Spam: {stats['spam']} ({stats['spam_pct']:.2f}%)\n")
                f.write(f"  Ham: {stats['ham']} ({stats['ham_pct']:.2f}%)\n")
                f.write(f"  Avg text length: {stats['avg_text_length']:.2f}\n")
            
            f.write(f"\nCombined Dataset Statistics:\n")
            f.write("-"*60 + "\n")
            f.write(f"Total: {combined_stats['total']}\n")
            f.write(f"Spam: {combined_stats['spam']} ({combined_stats['spam_pct']:.2f}%)\n")
            f.write(f"Ham: {combined_stats['ham']} ({combined_stats['ham_pct']:.2f}%)\n")
            f.write(f"Avg text length: {combined_stats['avg_text_length']:.2f}\n")
            
            if combined_stats['spam_pct'] > 65 or combined_stats['ham_pct'] > 65:
                f.write(f"\nWARNING: Class imbalance detected. Using class_weight='balanced' in training.\n")
            
            if include_sms:
                f.write(f"\nNOTE: SMS dataset included for ablation testing only.\n")
                f.write(f"SMS writing style is short and may cause domain shift.\n")
        
        logger.info(f"Dataset report saved to {report_path}")
        
        return combined_df
    
    def get_leave_one_out_splits(self, df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame, str]]:
        """
        Generate leave-one-dataset-out splits for domain shift testing.
        Returns list of (train_df, test_df, left_out_dataset_name).
        """
        splits = []
        datasets = df['source_dataset'].unique()
        
        for dataset in datasets:
            train_df = df[df['source_dataset'] != dataset].copy()
            test_df = df[df['source_dataset'] == dataset].copy()
            splits.append((train_df, test_df, dataset))
            logger.info(f"Leave-one-out split: left out '{dataset}' - train: {len(train_df)}, test: {len(test_df)}")
        
        return splits


def main():
    """Main function to run the data pipeline."""
    # Set paths
    script_dir = Path(__file__).parent.parent
    raw_data_dir = script_dir / 'data' / 'raw'
    processed_data_dir = script_dir / 'data' / 'processed'
    
    # Initialize pipeline
    pipeline = DataPipeline(raw_data_dir, processed_data_dir)
    
    # Combine datasets (SMS excluded by default)
    combined_df = pipeline.combine_datasets(include_sms=False)
    
    # Generate leave-one-out splits
    if len(combined_df) > 0:
        logger.info("\nGenerating leave-one-dataset-out splits...")
        splits = pipeline.get_leave_one_out_splits(combined_df)
        logger.info(f"Generated {len(splits)} leave-one-out splits for domain shift testing.")
    
    logger.info("\nData pipeline complete!")
    return combined_df


if __name__ == '__main__':
    main()
