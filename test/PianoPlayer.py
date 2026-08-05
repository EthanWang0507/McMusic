import fluidsynth
import time
import math
import threading


class PianoPlayer:
    def __init__(self, sf2_path: str, samplerate: int = 44100, gain: float = 0.8):
        """
        初始化播放器，同时支持钢琴（通道0）和打击乐（通道9）
        :param sf2_path: SF2音色库绝对路径
        :param samplerate: 采样率
        :param gain: 全局音量增益 0.0~2.0
        """
        self.synth = fluidsynth.Synth(samplerate=samplerate, gain=gain)
        self.synth.start(driver="dsound")  # macOS改coreaudio，Linux改alsa

        # 加载音色库
        self.sf_id = self.synth.sfload(sf2_path)
        if self.sf_id == -1:
            self.synth.delete()
            raise FileNotFoundError(f"SF2加载失败：{sf2_path}")

        # 通道0：加载钢琴音色（旋律乐器）
        self.synth.program_select(chan=0, sfid=self.sf_id, bank=0, preset=0)

        # 通道9：加载GM标准鼓组（打击乐专用通道，0基编号）
        # GM标准鼓组对应 bank=128，preset=0
        self.synth.program_select(chan=9, sfid=self.sf_id, bank=128, preset=0)

        self._running = True

    def _note_release_task(self, channel: int, pitch: int, duration: float):
        """后台守护线程：等待音符时长后自动发送note_off（旋律乐器用）"""
        time.sleep(duration)
        if self._running:
            self.synth.noteoff(channel, pitch)

    def play_note(
            self,
            pitch: int,
            velocity: int = 100,
            duration: float = 1.0,
            channel: int = 0,
            blocking: bool = False
    ):
        """
        播放旋律乐器音符（钢琴等）
        :param pitch: MIDI音高编号 0~127
        :param velocity: 按键力度 1~127
        :param duration: 音符按下时长（秒）
        :param channel: MIDI通道号（旋律乐器建议用0）
        :param blocking: 是否阻塞
        """
        pitch = max(0, min(127, int(pitch)))
        velocity = max(1, min(127, int(velocity)))

        self.synth.noteon(channel, pitch, velocity)
        if blocking:
            time.sleep(duration)
            self.synth.noteoff(channel, pitch)
            time.sleep(0.1)
        else:
            t = threading.Thread(
                target=self._note_release_task,
                args=(channel, pitch, duration),
                daemon=True
            )
            t.start()

    def play_drum(self, drum_note: int, velocity: int = 100):
        """
        播放打击乐（鼓组）专用方法
        :param drum_note: 打击乐音符编号（如36=底鼓，38=军鼓，42=闭合踩镲）
        :param velocity: 击打力度 1~127
        """
        drum_note = max(0, min(127, int(drum_note)))
        velocity = max(1, min(127, int(velocity)))
        # 打击乐固定发往通道9，无需note_off（One-Shot采样自动播放完整）
        self.synth.noteon(9, drum_note, velocity)

    def stop_all_notes(self, channel: int = 0):
        """立即停止指定通道的所有正在播放的音符"""
        if self._running:
            self.synth.cc(channel, 123, 0)

    @staticmethod
    def ms_delay(ms: float):
        """混合模式高精度毫秒延迟"""
        total_sec = ms / 1000.0
        end_time = time.perf_counter() + total_sec
        if total_sec > 0.002:
            time.sleep(total_sec - 0.002)
        while time.perf_counter() < end_time:
            pass

    @staticmethod
    def ms_delay_busy(ms: float):
        """纯忙等待超高精度延迟（仅短延迟使用）"""
        target = ms / 1000.0
        start = time.perf_counter()
        while time.perf_counter() - start < target:
            pass

    def freq_to_midi(self, freq: float) -> int:
        """频率(Hz)转MIDI音高编号"""
        return round(69 + 12 * math.log2(freq / 440))

    def close(self):
        """安全释放所有资源"""
        self._running = False
        self.stop_all_notes(0)
        self.stop_all_notes(9)
        time.sleep(0.2)
        self.synth.delete()


if __name__ == "__main__":
    player = PianoPlayer(r"MS Basic.sf2")

    # 测试打击乐：底鼓+军鼓+踩镲的简单动次打次
    # 36=底鼓  38=军鼓  42=闭合踩镲
    for _ in range(4):  # 4拍循环
        player.play_drum(36, velocity=110)  # 底鼓
        player.play_drum(42, velocity=80)  # 踩镲
        player.ms_delay_busy(250)  # 250ms间隔

        player.play_drum(42, velocity=75)  # 踩镲
        player.ms_delay_busy(250)

        player.play_drum(38, velocity=105)  # 军鼓
        player.play_drum(42, velocity=80)  # 踩镲
        player.ms_delay_busy(250)

        player.play_drum(42, velocity=75)  # 踩镲
        player.ms_delay_busy(250)

    time.sleep(1)  # 等待鼓声音尾播放完
    player.close()