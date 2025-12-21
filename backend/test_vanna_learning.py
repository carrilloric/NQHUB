#!/usr/bin/env python3
"""
Test Vanna.AI Learning Progress

This script shows:
1. How many queries Vanna has learned
2. What training data exists
3. Similar queries for a given question
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.assistant.tools.vanna_monitor import get_vanna_monitor
from app.assistant.tools.vanna_sql import get_vanna_client
import json


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    print("🔍 Vanna.AI Learning Progress Monitor\n")

    # Initialize monitor
    monitor = get_vanna_monitor()

    # 1. Get training statistics
    print_section("📊 Training Statistics")
    stats = monitor.get_training_stats()

    if stats["status"] == "unavailable":
        print(f"⚠️  {stats['message']}")
        print("\nVanna hasn't been initialized yet. Run a query first!")
        return

    print(f"Status: {stats['status']}")
    print(f"ChromaDB Path: {stats['chroma_path']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"DDL Schemas: {stats['total_ddl']}")
    print(f"SQL Examples: {stats['total_sql_examples']}")
    print(f"Documentation: {stats['total_documentation']}")

    print("\nCollections:")
    for col in stats['collections']:
        print(f"  - {col['name']}: {col['count']} documents")

    # 2. Get learned queries
    print_section("📚 Learned Queries (Last 10)")
    queries = monitor.get_learned_queries(limit=10)

    if not queries:
        print("No queries learned yet. Vanna will learn as you use it!")
    else:
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. ID: {query['id']}")
            print(f"   Content: {query['content'][:100]}...")
            if query['metadata']:
                print(f"   Metadata: {query['metadata']}")

    # 3. Test similarity search
    print_section("🔎 Similarity Search Test")
    test_questions = [
        "How many FVGs are there?",
        "Show me bullish order blocks",
        "What liquidity pools were swept?"
    ]

    for question in test_questions:
        print(f"\nQuestion: \"{question}\"")
        similar = monitor.get_similar_queries(question, limit=3)

        if similar:
            print("  Similar queries found:")
            for j, sim in enumerate(similar, 1):
                distance = sim.get('distance', 'N/A')
                content_preview = sim['content'][:80]
                print(f"    {j}. Distance: {distance:.4f} - {content_preview}...")
        else:
            print("  No similar queries found")

    # 4. Export training data
    print_section("💾 Export Training Data")
    export_path = "/tmp/vanna_training_export.json"
    success = monitor.export_training_data(export_path)

    if success:
        print(f"✅ Training data exported to: {export_path}")
        print(f"\nYou can inspect the file with:")
        print(f"  cat {export_path} | python3 -m json.tool | less")
    else:
        print("❌ Failed to export training data")

    # 5. Test live query generation
    print_section("🧪 Live Query Generation Test")
    vanna = get_vanna_client()

    if not vanna.vn:
        print("⚠️  Vanna client not available")
        return

    test_query = "How many FVGs are in the database?"
    print(f"Question: \"{test_query}\"")
    print("Generating SQL...")

    sql = vanna.generate_sql(test_query)
    print(f"\n✅ Generated SQL:")
    print(f"   {sql}")

    # Show what training examples were used
    similar = monitor.get_similar_queries(test_query, limit=3)
    if similar:
        print(f"\n📖 Vanna used these similar examples:")
        for i, sim in enumerate(similar, 1):
            print(f"   {i}. {sim['content'][:60]}... (distance: {sim.get('distance', 'N/A'):.4f})")

    print_section("✨ Summary")
    print("Vanna learns in two ways:")
    print("1. Pre-trained examples: 20+ queries we added in vanna_sql.py")
    print("2. Auto-training: Every successful query is saved automatically")
    print("\nThe more you use it, the smarter it gets! 🚀")
    print(f"\nCurrent learning: {stats['total_documents']} total examples")


if __name__ == "__main__":
    main()
