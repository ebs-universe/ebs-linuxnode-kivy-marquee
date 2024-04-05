

from twisted.internet import task
from twisted.internet.defer import Deferred

from kivy_garden.ebs.core.colors import color_set_alpha
from kivy_garden.ebs.marquee import MarqueeLabel
from ebs.linuxnode.gui.kivy.core.basenode import BaseIoTNodeGui


class MarqueeInterrupted(Exception):
    pass


class MarqueeBusy(Exception):
    def __init__(self, now_playing, collision_count):
        self.now_playing = now_playing
        self.collision_count = collision_count

    def __repr__(self):
        return "<MarqueeBusy Now Playing {0}" \
               "".format(self.now_playing)


class MarqueeGuiMixin(BaseIoTNodeGui):
    _gui_marquee_bgcolor = None
    _gui_marquee_color = None

    def __init__(self, *args, **kwargs):
        super(MarqueeGuiMixin, self).__init__(*args, **kwargs)
        self._gui_marquee = None
        self._marquee_is_default = False
        self._marquee_default_text = None
        self._marquee_default_task = None
        self._marquee_default_frequency = -1
        self._marquee_text = None
        self._marquee_deferred = None
        self._marquee_end_call = None
        self._marquee_collision_count = 0

    def marquee_show(self):
        if not self.gui_footer.parent:
            self.gui_footer.add_widget(self._gui_marquee)
            self.gui_footer_show('marquee')

    def marquee_hide(self):
        if self.gui_footer.parent:
            self.gui_footer_hide('marquee')
            self.gui_footer.remove_widget(self._gui_marquee)

    def marquee_play(self, text, bgcolor=None, color=None, duration=None, loop=False, weak=False):
        if self._marquee_deferred:
            if self._marquee_is_default:
                self.marquee_stop()
            elif weak:
                return None
            else:
                self._marquee_collision_count += 1
                if self._marquee_collision_count > 30:
                    self.marquee_stop(forced=True)
                raise MarqueeBusy(self._marquee_text,
                                  self._marquee_collision_count)
        self._marquee_collision_count = 0

        if bgcolor:
            self.gui_marquee.bgcolor = color_set_alpha(bgcolor, 0.6)
        if color:
            self.gui_marquee.color = color

        self.gui_marquee.text = text
        self.marquee_show()

        if duration:
            self._gui_marquee.start(loop=loop)
            self._marquee_end_call = self.reactor.callLater(duration, self.marquee_stop)
        else:
            self._gui_marquee.start(callback=self.marquee_stop, loop=loop)
        self._marquee_deferred = Deferred()
        return self._marquee_deferred

    def marquee_stop(self, forced=False):
        self._gui_marquee.stop()
        self.log.info("End Offset by {0} collisions."
                      "".format(self._marquee_collision_count))
        self._marquee_collision_count = 0
        self.marquee_hide()
        self.gui_marquee.bgcolor = self.marquee_default_bgcolor
        self.gui_marquee.color = self.marquee_default_color

        if self._marquee_end_call and self._marquee_end_call.active():
            self._marquee_end_call.cancel()

        if self._marquee_deferred:
            self._marquee_deferred.callback(forced)
            self._marquee_deferred = None

        self._marquee_is_default = False

        if self.marquee_default_text and not self._marquee_default_task:
            self._marquee_default_start()

    @property
    def marquee_default_bgcolor(self):
        return self._gui_marquee_bgcolor or color_set_alpha(self.gui_color_2, 0.5)

    @marquee_default_bgcolor.setter
    def marquee_default_bgcolor(self, value):
        # TODO Read / Write from config so it survives restart?
        if self.gui_marquee:
            self.gui_marquee.bgcolor = color_set_alpha(value, 0.5)
        self._gui_marquee_bgcolor = color_set_alpha(value, 0.5)

    @property
    def marquee_default_color(self):
        return self._gui_marquee_color or [1, 1, 1, 1]

    @marquee_default_color.setter
    def marquee_default_color(self, value):
        # TODO Read / Write from config so it survives restart?
        if self.gui_marquee:
            self.gui_marquee.color = color_set_alpha(value, 1)
        self._gui_marquee_color = color_set_alpha(value, 1)

    @property
    def marquee_default_text(self):
        if isinstance(self._marquee_default_text, str):
            return self._marquee_default_text
        elif isinstance(self._marquee_default_text, list):
            return ' | '.join(self._marquee_default_text)

    @marquee_default_text.setter
    def marquee_default_text(self, value):
        restart = False
        if value != self._marquee_default_text:
            if self._marquee_default_task:
                self._marquee_default_task.stop()
                self._marquee_default_task = None
            if self._marquee_is_default:
                self.marquee_stop()
            restart = True
        self._marquee_default_text = value
        if restart:
            self._marquee_default_start()

    @property
    def marquee_default_frequency(self):
        return self._marquee_default_frequency or 0

    @marquee_default_frequency.setter
    def marquee_default_frequency(self, value):
        restart = False
        if value != self._marquee_default_frequency:
            if self._marquee_default_task:
                self._marquee_default_task.stop()
                self._marquee_default_task = None
            if self._marquee_is_default:
                self.marquee_stop()
            restart = True
        self._marquee_default_frequency = value
        if restart:
            self._marquee_default_start()

    def _marquee_play_default_once(self):
        if not self.marquee_default_text or not self.marquee_default_frequency:
            self._marquee_default_task.stop()
            self._marquee_default_task = None
            return
        # TODO Manage rescheduling if this
        #  collides with a scheduled marquee
        self.marquee_play (
            text = self.marquee_default_text,
            loop = False, weak=True
        )
        self._marquee_is_default = True

    def _marquee_default_start(self):
        if not self.marquee_default_text or not self.marquee_default_frequency:
            return
        if self.marquee_default_frequency > 0:
            self._marquee_default_task = task.LoopingCall(
                self._marquee_play_default_once
            )
            self._marquee_default_task.start(
                self.marquee_default_frequency
            )
        else:
            self.marquee_play(text=self.marquee_default_text, weak=True)
            self._marquee_is_default = True

    @property
    def gui_marquee(self):
        if not self._gui_marquee:
            params = {'bgcolor': self.marquee_default_bgcolor,
                      'color': self.marquee_default_color,
                      'font_size': '30sp', **self.text_font_params}

            self._gui_marquee = MarqueeLabel(text='Marquee Text', **params)
            self.marquee_hide()
        return self._gui_marquee

    def start(self):
        super(MarqueeGuiMixin, self).start()
        self.reactor.callWhenRunning(self._marquee_default_start)

    def gui_setup(self):
        gui = super(MarqueeGuiMixin, self).gui_setup()
        _ = self.gui_marquee
        return gui
