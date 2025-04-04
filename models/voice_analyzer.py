import numpy as np
import librosa
import soundfile as sf
import io
import base64

class VoiceAnalyzer:
    def __init__(self):
        # Define ideal ranges for voice metrics
        self.ideal_ranges = {
            'speech_rate': (3, 5),  # words per second
            'pitch': (85, 255),     # Hz
            'volume': (-20, -5),     # dB
            'pause_ratio': (0.1, 0.3) # ratio of silence to speech
        }
    
    def base64_to_audio(self, base64_string, sample_rate=16000):
        """Convert base64 audio to numpy array"""
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
            
        audio_data = base64.b64decode(base64_string)
        audio_file = io.BytesIO(audio_data)
        
        try:
            y, sr = sf.read(audio_file)
            if sr != sample_rate:
                y = librosa.resample(y, orig_sr=sr, target_sr=sample_rate)
            return y, sample_rate
        except Exception as e:
            print(f"Error reading audio: {e}")
            return None, sample_rate
    
    def analyze_audio(self, audio_data):
        """Analyze audio characteristics"""
        if not audio_data:
            return None
        
        y, sr = self.base64_to_audio(audio_data)
        if y is None:
            return None
        
        # Calculate speech rate (words per second approximation)
        speech_rate = self._calculate_speech_rate(y, sr)
        
        # Calculate pitch (fundamental frequency)
        pitch = self._calculate_pitch(y, sr)
        
        # Calculate volume (dB)
        volume = self._calculate_volume(y)
        
        # Calculate pause ratio
        pause_ratio = self._calculate_pause_ratio(y, sr)
        
        # Calculate clarity (harmonic-to-noise ratio)
        clarity = self._calculate_clarity(y, sr)
        
        # Score each metric based on ideal ranges
        speech_rate_score = self._score_metric(speech_rate, self.ideal_ranges['speech_rate'])
        pitch_score = self._score_metric(pitch, self.ideal_ranges['pitch'])
        volume_score = self._score_metric(volume, self.ideal_ranges['volume'])
        pause_ratio_score = self._score_metric(pause_ratio, self.ideal_ranges['pause_ratio'])
        clarity_score = clarity  # Already in 0-100 range
        
        return {
            'speech_rate': speech_rate,
            'speech_rate_score': speech_rate_score,
            'pitch': pitch,
            'pitch_score': pitch_score,
            'volume': volume,
            'volume_score': volume_score,
            'pause_ratio': pause_ratio,
            'pause_ratio_score': pause_ratio_score,
            'clarity': clarity,
            'clarity_score': clarity_score,
            'total_score': np.mean([speech_rate_score, pitch_score, volume_score, 
                                  pause_ratio_score, clarity_score])
        }
    
    def _calculate_speech_rate(self, y, sr):
        """Estimate speech rate (words per second)"""
        # This is a simplified estimation - in practice you'd need speech-to-text
        # Here we estimate based on syllable rate
        
        # Calculate energy envelope
        energy = librosa.feature.rms(y=y)[0]
        energy_smooth = np.convolve(energy, np.ones(5)/5, mode='same')
        
        # Find peaks (approximate syllables)
        peaks = librosa.util.peak_pick(energy_smooth, 3, 3, 3, 3, 0.5, 5)
        
        # Estimate words per second (assuming ~2 syllables per word)
        if len(peaks) > 1:
            duration = len(y) / sr
            syllables_per_sec = len(peaks) / duration
            words_per_sec = syllables_per_sec / 2
            return words_per_sec
        return 3.5  # Default average
    
    def _calculate_pitch(self, y, sr):
        """Calculate average pitch (fundamental frequency)"""
        try:
            f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), 
                                   fmax=librosa.note_to_hz('C7'), sr=sr)
            f0 = f0[~np.isnan(f0)]
            if len(f0) > 0:
                return np.mean(f0)
        except:
            pass
        return 150  # Default average
    
    def _calculate_volume(self, y):
        """Calculate average volume in dB"""
        rms = np.sqrt(np.mean(y**2))
        if rms > 0:
            return 20 * np.log10(rms)
        return -30  # Very quiet
    
    def _calculate_pause_ratio(self, y, sr, threshold=0.02):
        """Calculate ratio of silence to speech"""
        # Split audio into voiced/unvoiced segments
        intervals = librosa.effects.split(y, top_db=30)
        
        # Calculate total voiced and unvoiced time
        voiced_time = sum(end - start for start, end in intervals) / sr
        total_time = len(y) / sr
        unvoiced_time = total_time - voiced_time
        
        if total_time > 0:
            return unvoiced_time / total_time
        return 0.2  # Default
    
    def _calculate_clarity(self, y, sr):
        """Calculate harmonic-to-noise ratio as clarity measure"""
        try:
            # Get harmonic and percussive components
            y_harmonic = librosa.effects.harmonic(y)
            y_percussive = librosa.effects.percussive(y)
            
            # Calculate energy ratio
            h_energy = np.mean(y_harmonic**2)
            p_energy = np.mean(y_percussive**2)
            
            if p_energy > 0:
                hnr = 10 * np.log10(h_energy / p_energy)
                # Convert to 0-100 scale (assuming -5 to 20 dB range)
                return min(100, max(0, (hnr + 5) * 4))
        except:
            pass
        return 75  # Default
    
    def _score_metric(self, value, ideal_range):
        """Score a metric based on how close it is to ideal range"""
        low, high = ideal_range
        
        if value < low:
            # Below range - linear penalty
            return max(0, 100 * (value / low))
        elif value > high:
            # Above range - linear penalty
            return max(0, 100 * (1 - (value - high) / high))
        else:
            # Within range - full score
            return 100
    
    def analyze_audio_sequence(self, audio_data_list):
        """Analyze a sequence of audio clips"""
        if not audio_data_list:
            return None
        
        # Analyze each audio clip
        clip_results = []
        for audio_data in audio_data_list:
            result = self.analyze_audio(audio_data)
            if result:
                clip_results.append(result)
        
        if not clip_results:
            return None
        
        # Aggregate results
        aggregated = {
            'avg_speech_rate': np.mean([r['speech_rate'] for r in clip_results]),
            'avg_pitch': np.mean([r['pitch'] for r in clip_results]),
            'avg_volume': np.mean([r['volume'] for r in clip_results]),
            'avg_pause_ratio': np.mean([r['pause_ratio'] for r in clip_results]),
            'avg_clarity': np.mean([r['clarity'] for r in clip_results]),
            'avg_total_score': np.mean([r['total_score'] for r in clip_results]),
            'consistency': self._calculate_consistency(clip_results)
        }
        
        return aggregated
    
    def _calculate_consistency(self, clip_results):
        """Calculate consistency of voice metrics across clips"""
        if len(clip_results) < 2:
            return 100  # Perfect if only one clip
        
        # Calculate coefficient of variation for each metric
        cv_speech_rate = np.std([r['speech_rate'] for r in clip_results]) / \
                        np.mean([r['speech_rate'] for r in clip_results])
        cv_pitch = np.std([r['pitch'] for r in clip_results]) / \
                  np.mean([r['pitch'] for r in clip_results])
        cv_volume = np.std([r['volume'] for r in clip_results]) / \
                   np.mean([r['volume'] for r in clip_results])
        
        # Average CV (lower is better)
        avg_cv = (cv_speech_rate + cv_pitch + cv_volume) / 3
        
        # Convert to 0-100 scale (assuming CV range 0-0.5)
        consistency = 100 - (avg_cv * 200)
        return max(0, min(100, consistency))