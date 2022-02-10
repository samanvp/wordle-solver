import re

INF = 10000
PUZZLE_SIZE = 5
GREEN_COEFF = 1.6
NUM_TOP_WORDS = 7

def loadWords(filename, verbose=False):
    words = []
    with open(filename, 'r') as f:
        words = f.read().splitlines()
    if verbose:
        print('Conpus contains {} words.'.format(len(words)))
    
    selectedWords = []
    for word in words:
        if len(word) != PUZZLE_SIZE or word.find('-') != -1:
            continue
        selectedWords.append(word)

    if verbose:
        print('Corpus contains {} correct words with length {}'.format(len(selectedWords), PUZZLE_SIZE))
    return selectedWords

def countLetters (words):
    counts = dict()
    for word in words:
        for i in range(PUZZLE_SIZE):
            key = (i, word[i])
            if counts.get(key):
                counts[key] += 1
            else:
                counts[key] = 1

            # In (-1, *) keys we store position independent letter weights
            key = (-1, word[i])
            if counts.get(key):
                counts[key] += 1
            else:
                counts[key] = 1

    return counts

def getScore(word, counts, verbose=False):
    scores = []
    for i in range(PUZZLE_SIZE):
        letter = word[i]
        key = (i, letter)
        if counts.get(key):
            scores.append(counts[key])
    
    wordList = list(word)
    for letter in wordList:
        dups = [i for i, x in enumerate(wordList) if x == letter]
        if len(dups) > 1:
            subScores = [scores[i] for i in dups]
            keep = subScores.index(max(subScores))
            for i in range(len(dups)):
                if i != keep:
                    scores[dups[i]] = 0

    score = sum(scores)
    if verbose :
        print(word, ':', score)
    return score

def findTopWord(counts, words):
    scores = []
    for word in words:
        scores.append(getScore(word, counts))

    topIndices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:NUM_TOP_WORDS]

    print('Best {} words are:'.format(NUM_TOP_WORDS))
    for i in range(len(topIndices)):
        print('({}) >>>>>>> {} <<<<<<< score: {}'.format(i+1, words[topIndices[i]], scores[topIndices[i]]))
    return [words[i] for i in topIndices]

def validateFeedback():
    validFeedback = False
    feedback = ''
    print('Feedback: ', end='')
    while(not validFeedback):
        feedback = input()
        if len(feedback) != PUZZLE_SIZE or not re.fullmatch(r'[BbYyGg]*', feedback):
            print('Wrong feedback format, please try again:')
            continue
        validFeedback = True
    return feedback

def parseFeedback(word, feedback):
    blacks = set()
    yellows = [None] * PUZZLE_SIZE
    greens = [None] * PUZZLE_SIZE
    for i in range(PUZZLE_SIZE):
        f = feedback[i]
        if f in ('B', 'b'):
            blacks.add(word[i])
        if f in ('Y', 'y'):
            yellows[i] = word[i]
        if f in ('G', 'g'):
            greens[i] = word[i]
    return (greens, yellows, blacks)    

def updateState(greens, yellows, latestGreens, latestYellows):
    newGreens = [None] * PUZZLE_SIZE
    newYellows = [None] * PUZZLE_SIZE
    removedYellows = set()

    # First update the Greens
    for i in range(PUZZLE_SIZE):
        if latestGreens[i]:
            if greens[i]:
                if greens[i] != latestGreens[i]:
                    raise ValueError('Position {} was Green letter {} and now it is {}'.format(i, greens[i], latestGreens[i]))
            else:
                newGreenLetter = latestGreens[i]
                greens[i] = newGreenLetter
                newGreens[i] = newGreenLetter
                # Now find out whether we previosly have seen this letter as a yellow one?
                for j in range(PUZZLE_SIZE):
                    if newGreenLetter in yellows[j]:
                        removedYellows.add(newGreenLetter)
                        yellows[j].remove(newGreenLetter)
    # Next update the Yellows
    for i in range(PUZZLE_SIZE):
        if latestYellows[i]:
            if not latestYellows[i] in yellows[i]:
                newYellowLetter = latestYellows[i]
                yellows[i].append(newYellowLetter)
                newYellows[i] = newYellowLetter
    return (newGreens, newYellows, removedYellows)

def updateWeights(guessNo, counts, greens, newGreens, newYellows, latestBlacks, removedYellows):
    for letter in latestBlacks:
        for i in range(PUZZLE_SIZE):
            key = (i, letter)
            counts[key] = -1 * PUZZLE_SIZE * INF

    # Reverse the change made by an old Yellow letter
    for removedYellowLetter in removedYellows:
        for j in range(PUZZLE_SIZE):
            key = (j, removedYellowLetter)
            if counts[key] < 0:
                continue
            else:
                counts[key] = int(counts[(-1, removedYellowLetter)] / PUZZLE_SIZE)

    # Apply new Yellows
    missingLettersCount = sum(elem is None for elem in greens)
    for i in range(PUZZLE_SIZE):
        if newYellows[i]:
            newYellowLetter = newYellows[i]
            key = (i, newYellowLetter)
            counts[key] = -1 * PUZZLE_SIZE * INF
            for j in range(PUZZLE_SIZE):
                if j == i or greens[j]:
                    continue
                else:
                    key = (j, newYellowLetter)
                    if counts[key] > 0:
                        counts[key] = int(INF / missingLettersCount)

    # Apply Greens
    if guessNo > 3 or missingLettersCount <= 2:
        # We aggresivly set all green weights to converge faster
        for i in range(PUZZLE_SIZE):
            if greens[i]:
                counts[(i, greens[i])] = INF
    else:
        for i in range(PUZZLE_SIZE):
            if newGreens[i]:
                newGreenLetter = newGreens[i]
                key = (i, newGreenLetter)
                counts[key] = int(counts[key] * GREEN_COEFF)

def selectedTopWord():
    selection = -1
    while(selection < 1 or selection > NUM_TOP_WORDS):
        print('Which word you used (1, 2, 3, ..)? ', end='')
        try:
            selection = int(input())
        except:
            print('Please enter a value between 1 and {}'.format(NUM_TOP_WORDS))
    return selection - 1 # This program might be used by someome other than a programmer :D

def playGame(corpusFile, verbose=False):
    words = loadWords(corpusFile, True)
    counts = countLetters(words)

    greens = [None] * PUZZLE_SIZE
    yellows = [ [] for _ in range(PUZZLE_SIZE) ]
    guessNo = 0
    feedback = ''
    while(feedback != 'ggggg'):
        guessNo += 1
        TopWords = findTopWord(counts, words)
        selectedWord = selectedTopWord()
        feedback = validateFeedback()
        (latestGreens, latestYellows, latestBlacks) = parseFeedback(TopWords[selectedWord], feedback)
        (newGreens, newYellows, removedYellows) = updateState(greens, yellows, latestGreens, latestYellows)
        updateWeights(guessNo, counts, greens, newGreens, newYellows, latestBlacks, removedYellows)

        if verbose:
            print('Current yellows: ')
            for item in yellows:
                if item:
                    print(item[0])
            print('Current Greens: ')
            for item in greens:
                if item:
                    print(item[0])
    print('Solved by {} guesses!'.format(guessNo))

def main():
    # For English use: './sgb-words.txt'
    # For Russian use: './Russian-words.txt'
    corpusFile = './sgb-words.txt'
    playGame(corpusFile)

if __name__ == '__main__':
    main()

