#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from song_editor.ui.enhanced_lyrics_editor import RhymeAnalyzer
import pronouncing

def test_rhyme_analysis():
    analyzer = RhymeAnalyzer()
    
    # Test words from user's example
    test_words = ['hello', 'today', 'world', 'how', 'are', 'you', 'I', 'hope', 'well']
    
    print("Testing rhyme analysis for words:")
    print("hello & today -> should be red (perfect rhymes)")
    print("world how are you I hope you are well -> should be green (near rhymes)")
    print()
    
    # Test perfect rhymes
    print("=== PERFECT RHYMES ===")
    for i, word1 in enumerate(test_words):
        for j, word2 in enumerate(test_words):
            if i != j:
                if analyzer.are_perfect_rhymes(word1, word2):
                    print(f"PERFECT: '{word1}' and '{word2}'")
    
    print("\n=== NEAR RHYMES ===")
    for i, word1 in enumerate(test_words):
        for j, word2 in enumerate(test_words):
            if i != j:
                if analyzer.are_near_rhymes(word1, word2):
                    print(f"NEAR: '{word1}' and '{word2}'")
    
    print("\n=== RHYME KEYS ===")
    for word in test_words:
        rhyme_key = analyzer.rhyme_key(word)
        near_key = analyzer.near_rhyme_key(word)
        print(f"'{word}': rhyme_key='{rhyme_key}', near_key='{near_key}'")
    
    print("\n=== DETAILED HELLO vs HOPE ANALYSIS ===")
    hello_phones = pronouncing.phones_for_word('hello')
    hope_phones = pronouncing.phones_for_word('hope')
    print(f"hello phones: {hello_phones}")
    print(f"hope phones: {hope_phones}")
    
    if hello_phones and hope_phones:
        hello_rhyme = pronouncing.rhyming_part(hello_phones[0])
        hope_rhyme = pronouncing.rhyming_part(hope_phones[0])
        print(f"hello rhyming part: {hello_rhyme}")
        print(f"hope rhyming part: {hope_rhyme}")
        print(f"Are they the same? {hello_rhyme == hope_rhyme}")
        
        # Check if they're in each other's rhyme lists
        hello_rhymes = pronouncing.rhymes('hello')
        hope_rhymes = pronouncing.rhymes('hope')
        print(f"'hope' in hello's rhymes: {'hope' in hello_rhymes}")
        print(f"'hello' in hope's rhymes: {'hello' in hope_rhymes}")

if __name__ == "__main__":
    test_rhyme_analysis()
