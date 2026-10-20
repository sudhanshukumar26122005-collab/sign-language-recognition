import time

class WordBuilder:
    def __init__(self, hold_seconds=0.6, grace_seconds=0.25):
        self.word = ""
        self.candidate_letter = ""
        self.letter_start_time = None
        self.last_seen_time = None
        self.committed = False
        self.hold_seconds = hold_seconds
        self.grace_seconds = grace_seconds

        self.fist_start_time = None
        self.fist_committed = False
        self.progress = 0.0

    def update(self, letter, fingers):
        now = time.time()
        is_fist = (fingers == [0, 0, 0, 0, 0])

        # 1. Handle non-fist letter detection
        if letter and not is_fist:
            self.fist_start_time = None
            self.fist_committed = False

            if letter != self.candidate_letter:
                # Switched to a new letter
                self.candidate_letter = letter
                self.letter_start_time = now
                self.last_seen_time = now
                self.committed = False
                self.progress = 0.0
            else:
                # Same letter sustained
                self.last_seen_time = now
                if not self.committed and self.letter_start_time is not None:
                    elapsed = now - self.letter_start_time
                    self.progress = min(1.0, elapsed / self.hold_seconds)
                    if elapsed >= self.hold_seconds:
                        self.word += letter
                        self.committed = True
                        self.progress = 1.0

        # 2. Handle fist (space between words)
        elif is_fist:
            self.progress = 0.0
            self.candidate_letter = ""
            self.letter_start_time = None

            if self.fist_start_time is None:
                self.fist_start_time = now
            elif (now - self.fist_start_time > 0.6) and not self.fist_committed:
                if self.word.strip() and not self.word.endswith(" "):
                    self.word += " "
                    self.fist_committed = True

        # 3. Neither recognized letter nor fist (jitter or transitional frames)
        else:
            # If we were tracking a candidate, allow a short grace window for single-frame dropouts
            if self.last_seen_time and (now - self.last_seen_time < self.grace_seconds):
                # Still within grace window - maintain candidate and progress
                pass
            else:
                # Grace window expired - reset progress
                self.candidate_letter = ""
                self.letter_start_time = None
                self.committed = False
                self.progress = 0.0

            if not is_fist:
                self.fist_start_time = None
                self.fist_committed = False

        return self.word

    def clear(self):
        self.word = ""
        self.candidate_letter = ""
        self.letter_start_time = None
        self.last_seen_time = None
        self.committed = False
        self.fist_start_time = None
        self.fist_committed = False
        self.progress = 0.0

    def backspace(self):
        if self.word:
            self.word = self.word[:-1]
        self.candidate_letter = ""
        self.letter_start_time = None
        self.last_seen_time = None
        self.committed = False
        self.progress = 0.0
