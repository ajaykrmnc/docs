# Design a Search Autocomplete System
**Difficulty:** Hard | **Companies:** Google, Amazon, Microsoft, LinkedIn

---

## Problem Statement

Design a search autocomplete/typeahead system that provides real-time suggestions as users type, with ranking 
based on frequency, recency, and personalization.

---

## Requirements

### Functional Requirements
1. Return top-k suggestions as user types
2. Trie-based prefix matching
3. Ranking based on frequency and recency
4. Personalized suggestions per user
5. Support for fuzzy matching (typo tolerance)
6. Phrase suggestions (not just single words)
7. Real-time updates when new searches occur

### Non-Functional Requirements
1. Ultra-low latency (< 50ms)
2. High availability
3. Eventually consistent updates

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AutocompleteService                          │
├─────────────────────────────────────────────────────────────────┤
│ - trie: Trie                                                    │
│ - ranker: SuggestionRanker                                      │
│ - userHistory: UserHistoryStore                                 │
│ - fuzzyMatcher: FuzzyMatcher                                    │
│ - cache: SuggestionCache                                        │
├─────────────────────────────────────────────────────────────────┤
│ + getSuggestions(prefix: String, userId: String, k: int): List  │
│ + recordSearch(query: String, userId: String): void             │
│ + addTerm(term: String, weight: long): void                     │
│ + removeTerm(term: String): void                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Trie                                   │
├─────────────────────────────────────────────────────────────────┤
│ - root: TrieNode                                                │
├─────────────────────────────────────────────────────────────────┤
│ + insert(word: String, weight: long): void                      │
│ + search(prefix: String): List<TrieNode>                        │
│ + getTopK(prefix: String, k: int): List<Suggestion>             │
│ + delete(word: String): boolean                                 │
│ + update(word: String, weight: long): void                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        TrieNode                                 │
├─────────────────────────────────────────────────────────────────┤
│ - children: Map<Character, TrieNode>                            │
│ - isEndOfWord: boolean                                          │
│ - word: String                                                  │
│ - weight: long                                                  │
│ - topSuggestions: List<Suggestion>                              │
├─────────────────────────────────────────────────────────────────┤
│ + getChild(c: char): TrieNode                                   │
│ + addChild(c: char): TrieNode                                   │
│ + updateTopSuggestions(suggestion: Suggestion, k: int): void    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Implementations

### 1. TrieNode with Precomputed Top-K
```java
public class TrieNode {
    private final Map<Character, TrieNode> children;
    private boolean isEndOfWord;
    private String word;
    private long weight;
    private final PriorityQueue<Suggestion> topSuggestions;
    private final int maxSuggestions;
    
    public TrieNode(int k) {
        this.children = new HashMap<>();
        this.isEndOfWord = false;
        this.maxSuggestions = k;
        this.topSuggestions = new PriorityQueue<>(
            Comparator.comparingLong(Suggestion::getScore)
        );  // Min-heap
    }
    
    public TrieNode getChild(char c) {
        return children.get(c);
    }
    
    public TrieNode addChild(char c) {
        return children.computeIfAbsent(c, k -> new TrieNode(maxSuggestions));
    }
    
    public void updateTopSuggestions(Suggestion suggestion) {
        // Remove if exists (to update)
        topSuggestions.removeIf(s -> s.getTerm().equals(suggestion.getTerm()));
        topSuggestions.offer(suggestion);
        
        // Keep only top-k
        while (topSuggestions.size() > maxSuggestions) {
            topSuggestions.poll();
        }
    }
    
    public List<Suggestion> getTopSuggestions() {
        List<Suggestion> result = new ArrayList<>(topSuggestions);
        result.sort(Comparator.comparingLong(Suggestion::getScore).reversed());
        return result;
    }
}
```

### 2. Trie Implementation
```java
public class Trie {
    private final TrieNode root;
    private final int k;
    private final ReentrantReadWriteLock lock;
    
    public Trie(int k) {
        this.root = new TrieNode(k);
        this.k = k;
        this.lock = new ReentrantReadWriteLock();
    }
    
    public void insert(String word, long weight) {
        lock.writeLock().lock();
        try {
            TrieNode current = root;
            Suggestion suggestion = new Suggestion(word, weight);
            
            for (char c : word.toLowerCase().toCharArray()) {
                current.updateTopSuggestions(suggestion);
                current = current.addChild(c);
            }
            
            current.setEndOfWord(true);
            current.setWord(word);
            current.setWeight(weight);
            current.updateTopSuggestions(suggestion);
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    public List<Suggestion> getTopK(String prefix, int k) {
        lock.readLock().lock();
        try {
            TrieNode node = findNode(prefix.toLowerCase());
            if (node == null) return List.of();
            
            return node.getTopSuggestions().stream()
                .limit(k)
                .collect(Collectors.toList());
        } finally {
            lock.readLock().unlock();
        }
    }
    
    private TrieNode findNode(String prefix) {
        TrieNode current = root;
        for (char c : prefix.toCharArray()) {
            current = current.getChild(c);
            if (current == null) return null;
        }
        return current;
    }
    
    public void updateWeight(String word, long delta) {
        lock.writeLock().lock();
        try {
            TrieNode node = findNode(word.toLowerCase());
            if (node != null && node.isEndOfWord()) {
                long newWeight = node.getWeight() + delta;
                insert(word, newWeight);  // Re-insert to update all ancestors
            }
        } finally {
            lock.writeLock().unlock();
        }
    }
}
```

### 3. Suggestion Ranker with Multiple Signals
```java
public class SuggestionRanker {
    private final double frequencyWeight;
    private final double recencyWeight;
    private final double personalWeight;
    
    public SuggestionRanker(double freq, double recency, double personal) {
        this.frequencyWeight = freq;
        this.recencyWeight = recency;
        this.personalWeight = personal;
    }
    
    public List<Suggestion> rank(List<Suggestion> suggestions, 
                                  UserHistory history, 
                                  int k) {
        return suggestions.stream()
            .map(s -> scoreAndWrap(s, history))
            .sorted(Comparator.comparingDouble(ScoredSuggestion::getScore).reversed())
            .limit(k)
            .map(ScoredSuggestion::getSuggestion)
            .collect(Collectors.toList());
    }
    
    private ScoredSuggestion scoreAndWrap(Suggestion s, UserHistory history) {
        double score = 0;
        
        // Global frequency score (log scale to prevent domination)
        score += frequencyWeight * Math.log1p(s.getScore());
        
        // Recency boost (decay over time)
        if (s.getLastSearchTime() != null) {
            long hoursSinceSearch = Duration.between(s.getLastSearchTime(), Instant.now()).toHours();
            score += recencyWeight * Math.exp(-hoursSinceSearch / 24.0);
        }
        
        // Personal history boost
        if (history != null) {
            int userSearchCount = history.getSearchCount(s.getTerm());
            score += personalWeight * Math.log1p(userSearchCount);
        }
        
        return new ScoredSuggestion(s, score);
    }
}
```

### 4. Fuzzy Matcher for Typo Tolerance
```java
public class FuzzyMatcher {
    private final Trie trie;
    private final int maxEditDistance;
    
    public FuzzyMatcher(Trie trie, int maxDistance) {
        this.trie = trie;
        this.maxEditDistance = maxDistance;
    }
    
    public List<Suggestion> fuzzySearch(String prefix, int k) {
        List<Suggestion> results = new ArrayList<>();
        fuzzySearchHelper(trie.getRoot(), prefix, 0, "", maxEditDistance, results);
        
        return results.stream()
            .sorted(Comparator.comparingLong(Suggestion::getScore).reversed())
            .limit(k)
            .collect(Collectors.toList());
    }
    
    private void fuzzySearchHelper(TrieNode node, String target, int index,
                                    String current, int remaining, 
                                    List<Suggestion> results) {
        if (remaining < 0) return;
        
        if (index == target.length()) {
            // Collect all words from this node
            collectWords(node, current, results);
            return;
        }
        
        char c = target.charAt(index);
        
        for (Map.Entry<Character, TrieNode> entry : node.getChildren().entrySet()) {
            char childChar = entry.getKey();
            TrieNode child = entry.getValue();
            
            if (childChar == c) {
                // Match: no edit needed
                fuzzySearchHelper(child, target, index + 1, 
                    current + childChar, remaining, results);
            } else {
                // Substitution
                fuzzySearchHelper(child, target, index + 1,
                    current + childChar, remaining - 1, results);
            }
            
            // Insertion (extra char in input)
            fuzzySearchHelper(child, target, index,
                current + childChar, remaining - 1, results);
        }
        
        // Deletion (missing char in input)
        fuzzySearchHelper(node, target, index + 1, current, remaining - 1, results);
    }
}
```

### 5. AutocompleteService
```java
public class AutocompleteService {
    private final Trie trie;
    private final SuggestionRanker ranker;
    private final UserHistoryStore historyStore;
    private final FuzzyMatcher fuzzyMatcher;
    private final Cache<String, List<Suggestion>> cache;
    
    public List<Suggestion> getSuggestions(String prefix, String userId, int k) {
        if (prefix == null || prefix.length() < 2) {
            return List.of();
        }
        
        // Check cache first
        String cacheKey = prefix.toLowerCase();
        List<Suggestion> cached = cache.get(cacheKey);
        
        List<Suggestion> suggestions;
        if (cached != null) {
            suggestions = new ArrayList<>(cached);
        } else {
            suggestions = trie.getTopK(prefix, k * 2);  // Get more for ranking
            
            // Try fuzzy if no exact matches
            if (suggestions.isEmpty()) {
                suggestions = fuzzyMatcher.fuzzySearch(prefix, k * 2);
            }
            
            cache.put(cacheKey, suggestions);
        }
        
        // Personalized ranking
        UserHistory history = userId != null ? historyStore.get(userId) : null;
        return ranker.rank(suggestions, history, k);
    }
    
    public void recordSearch(String query, String userId) {
        // Update global frequency
        trie.updateWeight(query, 1);
        
        // Update user history
        if (userId != null) {
            historyStore.recordSearch(userId, query);
        }
        
        // Invalidate cache for prefixes
        invalidatePrefixCache(query);
    }
}
```

