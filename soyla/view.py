# encoding: utf-8
import urwid

from .state import SoylaState


class MyListBox(urwid.ListBox):
    """
    Custom listbox that ignores all keypresses
    """
    def keypress(self, size, key):
        return key


class SoylaView(object):
    """
    Class handles drawing of and interacting with UI
    """
    PALETTE = [
        ('screen edge', 'black', 'black'),
        ('line', 'light gray', 'black'),
        ('main', 'light gray', 'black'),
        ('reversed', 'standout', ''),
        ('check', 'dark green', 'black'),
        ('text', 'white,bold', 'black'),
        ('state', 'dark green', 'black'),
        ('recording', 'light red', 'black'),
        ('instructions', 'light magenta', 'black'),
        ('status', 'yellow', 'black'),
    ]

    def __init__(self, model):
        """
        :param model: instance of SoylaModel
        """
        self.model = model
        self._init_widgets()
        self.update_line()

    def _init_widgets(self):
        """
        builds widget tree
        """
        status = self._status()
        sidebar = self._sidebar()
        main = self._main(status)

        vline = urwid.AttrMap(urwid.SolidFill(u'\u2502'), 'line')
        self._top = urwid.Columns([
            ('weight', 1, sidebar),
            ('fixed', 1, vline),
            ('weight', 2, main),
        ])
        bg = urwid.AttrMap(urwid.SolidFill(u"\u2592"), 'screen edge')
        w = urwid.LineBox(urwid.AttrMap(self._top, 'main'))
        w = urwid.AttrMap(w, 'line')
        self._overlay = urwid.Overlay(w, bg,
                                      ('fixed left', 1), ('fixed right', 1),
                                      ('fixed top', 0), ('fixed bottom', 0))

    def _status(self):
        """
        builds widgets for status line at the bottom
        :returns: urwid.Widget object
        """
        self._total_audio_text = urwid.Text('', align='right')
        self._audio_length_text = urwid.Text('', align='left')
        self._saved_text = urwid.Text('', align='center')
        status = urwid.Columns([
            ('weight', 1, self._audio_length_text),
            ('weight', 1, self._saved_text),
            ('weight', 1, self._total_audio_text),
        ])
        return urwid.AttrMap(status, 'status')

    def _main(self, status):
        """
        builds widgets for main window pane
        :param status: status line widgets
        :returns: urwid.Widget object
        """
        self._line_text = urwid.Text('', align='center')
        self._line_edit = urwid.Edit(align='center')
        self._line = urwid.WidgetPlaceholder(self._line_text)

        self._state_text = urwid.Text('', align='center')
        self._instructions_text = urwid.Text('', align='left')

        vline = urwid.AttrMap(urwid.SolidFill(u'\u2502'), 'line')
        hline = urwid.AttrMap(urwid.Divider('─'), 'line')

        state_instr = urwid.Columns([
            ('weight', 1, urwid.Filler(self._state_text)),
            ('fixed', 1, vline),
            ('weight', 1, urwid.Filler(urwid.Padding(self._instructions_text, 'center', width='pack'))),
        ])
        return urwid.Pile([
            ('weight', 1, urwid.AttrMap(urwid.Filler(self._line), 'text')),
            ('pack', hline),
            ('weight', 1, state_instr),
            ('pack', hline),
            (1, urwid.Padding(urwid.Filler(status), left=1, right=1)),
        ])

    def _format_line_for_sidebar(self, i):
        """
        format text for given line
        :param i: line index
        :returns: input for urwid.Text widget
        """
        check = '\u2714 ' if self.model.line_has_audio(i) else '  '
        return [('check', check), " {}. {}".format(i, self.model.get_lines()[i])]

    def _sidebar(self):
        """
        build sidebar widgets
        :returns: urwid.Widget object
        """
        text_lines = []
        for i in range(len(self.model.get_lines())):
            txt = self._format_line_for_sidebar(i)
            w = urwid.Text(txt, wrap='clip')
            w = urwid.AttrMap(w, None, focus_map='reversed')
            text_lines.append(w)
        self._line_list = text_lines
        self._line_listbox = MyListBox(urwid.SimpleFocusListWalker(self._line_list))
        return urwid.Padding(self._line_listbox, left=1, right=1)

    def _draw_line_text(self):
        """
        update displayed line text
        """
        self._line_text.set_text(self.model.get_current_line())

    def _draw_status(self):
        """
        update status line widgets
        """
        if self.model.cur_audio_length() is None:
            record_length = "No recording"
        else:
            record_length = "Recording length: {:.2f} seconds".format(self.model.cur_audio_length())
        self._audio_length_text.set_text(record_length)
        self._saved_text.set_text("")
        self._total_audio_text.set_text("Project audio length: {:.2f} seconds".format(self.model.audio_sum_length()))

    def update_state(self, state):
        """
        update displayed state and instructions text
        :param state: SoylaState object
        """
        txt = state.text()
        attr = 'state'
        if state == SoylaState.RECORDING:
            attr = 'recording'
        self._state_text.set_text((attr, txt))
        self._instructions_text.set_text(('instructions', state.instruction()))

    def update_line(self):
        """
        update displayed line and status widgets, update sidebar focus
        """
        self._draw_line_text()
        self._draw_status()
        self._line_listbox.set_focus(self.model.l_index)

    def update_sidebar_line(self, i):
        """
        update sidebar text for given line
        :param i: index of line
        """
        self._line_list[i].original_widget.set_text(self._format_line_for_sidebar(i))

    def show_saved(self):
        """
        show "Saved" text in status line
        """
        self._saved_text.set_text("Saved")

    def start_edit(self):
        """
        enter editing mode of currently selected line
        """
        txt = self.model.get_current_line()
        self._line.original_widget = self._line_edit
        self._line_edit.set_edit_text(txt)
        self._line_edit.set_edit_pos(len(txt))
        self._top.set_focus(2)

    def finish_edit(self):
        """
        finish editing
        :returns: edited text
        """
        self._line.original_widget = self._line_text
        self._top.set_focus(0)
        return self._line_edit.get_edit_text()

    def top_widget(self):
        """
        :returns: top widget in the hierarchy
        """
        return self._overlay
