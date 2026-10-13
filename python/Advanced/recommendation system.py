import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.linalg import svds
from typing import Dict, List, Tuple, Optional
import json
import pickle
from collections import defaultdict
import random

class RecommendationSystem:
    def __init__(self):
        self.user_item_matrix = None
        self.item_features = None
        self.user_factors = None
        self.item_factors = None
        self.item_similarity = None
        self.user_means = None
        self.item_means = None
        self.tfidf_vectorizer = TfidfVectorizer()
        self.is_trained = False
    
    def load_data(self, ratings_file: str, items_file: str):
        """Load ratings and item metadata"""
        # Load ratings data
        self.ratings_df = pd.read_csv(ratings_file)
        self.items_df = pd.read_csv(items_file)
        
        # Create user-item matrix
        self.user_item_matrix = self.ratings_df.pivot(
            index='user_id',
            columns='item_id',
            values='rating'
        ).fillna(0)
        
        # Store users and items
        self.users = self.user_item_matrix.index.tolist()
        self.items = self.user_item_matrix.columns.tolist()
        
        # Normalize ratings
        self.user_means = self.user_item_matrix.mean(axis=1)
        self.item_means = self.user_item_matrix.mean(axis=0)
        
        # Create item features from item metadata
        self._create_item_features()
        
        print(f"Loaded {len(self.users)} users and {len(self.items)} items")
    
    def _create_item_features(self):
        """Create feature vectors for content-based filtering"""
        # Combine item metadata into text for TF-IDF
        item_texts = []
        for _, item in self.items_df.iterrows():
            text = f"{item.get('title', '')} {item.get('genre', '')} {item.get('description', '')}"
            item_texts.append(text)
        
        # Create TF-IDF vectors
        self.item_features = self.tfidf_vectorizer.fit_transform(item_texts)
        
        # Calculate item similarity matrix
        self.item_similarity = cosine_similarity(self.item_features)
    
    def train_collaborative_filtering(self, n_factors: int = 50):
        """Train SVD model for collaborative filtering"""
        print("Training collaborative filtering model...")
        
        # Normalize user-item matrix
        matrix = self.user_item_matrix.values
        matrix_norm = matrix - self.user_means.values.reshape(-1, 1)
        
        # Perform SVD
        U, sigma, Vt = svds(matrix_norm, k=n_factors)
        
        # Convert to diagonal matrix
        sigma = np.diag(sigma)
        
        # Get user and item factors
        self.user_factors = U
        self.item_factors = Vt.T
        
        # Calculate predicted ratings
        self.predicted_ratings = np.dot(
            np.dot(self.user_factors, sigma),
            self.item_factors.T
        ) + self.user_means.values.reshape(-1, 1)
        
        self.is_trained = True
        print(f"Training complete. Factors: {n_factors}")
    
    def get_collaborative_recommendations(self, user_id: int, n: int = 10) -> List[Tuple[int, float]]:
        """Get recommendations using collaborative filtering"""
        if not self.is_trained:
            return []
        
        # Get user index
        try:
            user_idx = self.users.index(user_id)
        except ValueError:
            return []
        
        # Get user's ratings
        user_ratings = self.user_item_matrix.iloc[user_idx]
        rated_items = user_ratings[user_ratings > 0].index.tolist()
        
        # Get predicted ratings
        user_predictions = self.predicted_ratings[user_idx]
        
        # Create list of (item, rating) excluding already rated
        recommendations = []
        for i, item in enumerate(self.items):
            if item not in rated_items:
                recommendations.append((item, user_predictions[i]))
        
        # Sort by rating
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:n]
    
    def get_content_recommendations(self, item_id: int, n: int = 10) -> List[Tuple[int, float]]:
        """Get recommendations using content-based filtering"""
        if self.item_similarity is None:
            return []
        
        try:
            item_idx = self.items.index(item_id)
        except ValueError:
            return []
        
        # Get similarity scores for this item
        similarities = self.item_similarity[item_idx]
        
        # Create list of (item, similarity) excluding itself
        recommendations = []
        for i, item in enumerate(self.items):
            if i != item_idx:
                recommendations.append((item, similarities[i]))
        
        # Sort by similarity
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:n]
    
    def get_hybrid_recommendations(self, user_id: int, n: int = 10, alpha: float = 0.7) -> List[Tuple[int, float]]:
        """Hybrid recommendations combining collaborative and content-based"""
        # Get collaborative recommendations
        collab_recs = self.get_collaborative_recommendations(user_id, n=20)
        
        if not collab_recs:
            # Fallback to content-based if no collaborative data
            return self.get_popular_items(n)
        
        # Get content-based recommendations for each item
        hybrid_scores = {}
        for item_id, collab_score in collab_recs:
            content_recs = self.get_content_recommendations(item_id, n=10)
            
            # Content score for the original item
            content_score = 0
            for rec_item, sim in content_recs:
                if rec_item == item_id:
                    content_score = sim
                    break
            
            # Hybrid score (weighted average)
            hybrid_score = alpha * collab_score + (1 - alpha) * content_score
            hybrid_scores[item_id] = hybrid_score
        
        # Sort by hybrid score
        recommendations = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        
        return recommendations[:n]
    
    def get_popular_items(self, n: int = 10) -> List[Tuple[int, float]]:
        """Get most popular items based on average rating"""
        popular = self.item_means.nlargest(n)
        return [(item, score) for item, score in popular.items()]
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get user's preferences and rating patterns"""
        try:
            user_idx = self.users.index(user_id)
            user_ratings = self.user_item_matrix.iloc[user_idx]
            rated_items = user_ratings[user_ratings > 0]
            
            # Get average rating by genre
            genre_ratings = defaultdict(list)
            for item_id, rating in rated_items.items():
                if item_id in self.items_df['item_id'].values:
                    genres = self.items_df[self.items_df['item_id'] == item_id]['genre'].iloc[0]
                    for genre in genres.split(','):
                        genre_ratings[genre.strip()].append(rating)
            
            avg_genre_ratings = {genre: np.mean(ratings) for genre, ratings in genre_ratings.items()}
            
            return {
                'user_id': user_id,
                'total_ratings': len(rated_items),
                'average_rating': user_ratings[user_ratings > 0].mean(),
                'genre_preferences': dict(sorted(avg_genre_ratings.items(), key=lambda x: x[1], reverse=True)),
                'top_items': rated_items.nlargest(5).to_dict()
            }
        except:
            return {'user_id': user_id, 'error': 'User not found'}
    
    def evaluate_recommendations(self, test_data: pd.DataFrame, k: int = 10) -> Dict:
        """Evaluate recommendation quality using precision, recall, and NDCG"""
        print("Evaluating recommendations...")
        
        # Group test data by user
        test_by_user = test_data.groupby('user_id')
        
        precision_scores = []
        recall_scores = []
        ndcg_scores = []
        
        for user_id, group in test_by_user:
            # Get recommendations for this user
            recommendations = self.get_hybrid_recommendations(user_id, n=k)
            rec_items = [item for item, _ in recommendations]
            
            # Get actual items this user liked in test data
            actual_items = group[group['rating'] >= 4]['item_id'].tolist()
            
            if not actual_items:
                continue
            
            # Calculate precision and recall
            relevant_recs = len(set(rec_items) & set(actual_items))
            precision = relevant_recs / len(rec_items) if rec_items else 0
            recall = relevant_recs / len(actual_items) if actual_items else 0
            
            precision_scores.append(precision)
            recall_scores.append(recall)
            
            # Calculate NDCG
            dcg = 0
            idcg = 0
            
            for i, item in enumerate(rec_items[:k]):
                relevance = 1 if item in actual_items else 0
                dcg += relevance / np.log2(i + 2)
            
            # Ideal DCG
            for i in range(min(k, len(actual_items))):
                idcg += 1 / np.log2(i + 2)
            
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcg_scores.append(ndcg)
        
        return {
            'precision@k': np.mean(precision_scores),
            'recall@k': np.mean(recall_scores),
            'ndcg@k': np.mean(ndcg_scores),
            'f1_score': 2 * np.mean(precision_scores) * np.mean(recall_scores) / 
                       (np.mean(precision_scores) + np.mean(recall_scores)) if (np.mean(precision_scores) + np.mean(recall_scores)) > 0 else 0
        }
    
    def save_model(self, path: str):
        """Save trained model to disk"""
        model_data = {
            'user_factors': self.user_factors,
            'item_factors': self.item_factors,
            'user_means': self.user_means,
            'item_means': self.item_means,
            'predicted_ratings': self.predicted_ratings,
            'users': self.users,
            'items': self.items,
            'is_trained': self.is_trained
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load trained model from disk"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.user_factors = model_data['user_factors']
        self.item_factors = model_data['item_factors']
        self.user_means = model_data['user_means']
        self.item_means = model_data['item_means']
        self.predicted_ratings = model_data['predicted_ratings']
        self.users = model_data['users']
        self.items = model_data['items']
        self.is_trained = model_data['is_trained']
        
        print(f"Model loaded from {path}")

def generate_sample_data():
    """Generate sample recommendation data"""
    # Ratings data
    ratings_data = []
    items = [i for i in range(1, 101)]
    
    for user in range(1, 501):
        # Each user rates 10-30 items
        num_ratings = random.randint(10, 30)
        rated_items = random.sample(items, num_ratings)
        
        for item in rated_items:
            # Generate rating with some bias
            user_bias = random.normalvariate(0, 0.5)
            item_bias = random.normalvariate(0, 0.5)
            rating = min(5, max(1, 3 + user_bias + item_bias + random.normalvariate(0, 0.5)))
            ratings_data.append({
                'user_id': user,
                'item_id': item,
                'rating': round(rating, 1)
            })
    
    ratings_df = pd.DataFrame(ratings_data)
    ratings_df.to_csv('ratings.csv', index=False)
    
    # Items data
    genres = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Romance', 'Thriller', 'Documentary']
    items_data = []
    for i in range(1, 101):
        items_data.append({
            'item_id': i,
            'title': f'Item {i}',
            'genre': ','.join(random.sample(genres, random.randint(1, 3))),
            'description': f'Description for item {i}'
        })
    
    items_df = pd.DataFrame(items_data)
    items_df.to_csv('items.csv', index=False)
    
    print("Sample data generated: ratings.csv and items.csv")

async def main():
    print("=== Recommendation System ===")
    
    # Generate sample data if needed
    import os
    if not os.path.exists('ratings.csv'):
        generate_sample_data()
    
    # Create recommendation system
    rec_sys = RecommendationSystem()
    rec_sys.load_data('ratings.csv', 'items.csv')
    
    # Train model
    rec_sys.train_collaborative_filtering(n_factors=30)
    
    # Get recommendations for a user
    user_id = 1
    print(f"\nRecommendations for User {user_id}:")
    
    collaborative = rec_sys.get_collaborative_recommendations(user_id, n=5)
    print("Collaborative:", collaborative)
    
    hybrid = rec_sys.get_hybrid_recommendations(user_id, n=5)
    print("Hybrid:", hybrid)
    
    # Get user preferences
    preferences = rec_sys.get_user_preferences(user_id)
    print(f"\nUser {user_id} Preferences:")
    print(f"Total Ratings: {preferences['total_ratings']}")
    print(f"Average Rating: {preferences['average_rating']:.2f}")
    print(f"Top Genres: {list(preferences['genre_preferences'].keys())[:3]}")
    
    # Evaluate
    test_data = pd.read_csv('ratings.csv').sample(n=1000)
    evaluation = rec_sys.evaluate_recommendations(test_data)
    print("\nModel Evaluation:")
    for metric, value in evaluation.items():
        print(f"{metric}: {value:.4f}")
    
    # Save model
    rec_sys.save_model('recommendation_model.pkl')

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

# Install: pip install numpy pandas scikit-learn scipy