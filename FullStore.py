# By Misazam
# ba_meta require api 9

from __future__ import annotations

from typing import Any

import babase
import bauiv1 as bui
from baclassic._store import StoreSubsystem

SPECIAL_CHARACTERS: tuple[tuple[str, str], ...] = (
    ('characters.santa', 'Santa Claus'),
    ('characters.bunny', 'Easter Bunny'),
    ('characters.taobaomascot', 'Taobao Mascot'),
)
SPECIAL_CHARACTER_ITEMS = frozenset(item for item, _name in SPECIAL_CHARACTERS)
FULLSTORE_INVENTORY_ACTION = 'fullstore_buy_character'

_FULLSTORE_TEXTS: dict[str, dict[str, str]] = {
    'en': {
        'inventory_row_title': 'Special Characters',
        'already_owned_message': 'You already own that character.',
        'unavailable_message': (
            'This character does not have a published price right now.'
        ),
        'unrecognized_character': 'Unrecognized special character.',
        'owned_status': 'Owned',
        'no_price_status': 'No price now',
        'buy_with_tickets': 'Buy {price} tickets',
        'invalid_purchase_action': 'Invalid purchase action.',
        'tickets_count': 'Tickets: {tickets}',
        'already_owned_status': 'Already owned',
        'server_no_price': 'The server is not publishing a price right now',
        'unavailable_button': 'Unavailable',
        'price_with_tickets': 'Price: {price} tickets',
        'buy_button': 'Buy {price}',
    },
    'es': {
        'inventory_row_title': 'Personajes especiales',
        'already_owned_message': 'Ya tienes ese personaje.',
        'unavailable_message': (
            'Este personaje no tiene precio publicado ahora.'
        ),
        'unrecognized_character': 'Personaje especial no reconocido.',
        'owned_status': 'Comprado',
        'no_price_status': 'Sin precio ahora',
        'buy_with_tickets': 'Comprar {price} tickets',
        'invalid_purchase_action': 'Accion de compra invalida.',
        'tickets_count': 'Tickets: {tickets}',
        'already_owned_status': 'Ya comprado',
        'server_no_price': 'El servidor no esta publicando precio ahora',
        'unavailable_button': 'No disponible',
        'price_with_tickets': 'Precio: {price} tickets',
        'buy_button': 'Comprar {price}',
    },
}
FULLSTORE_INVENTORY_ROW_TITLES = tuple(
    texts['inventory_row_title'] for texts in _FULLSTORE_TEXTS.values()
)


def is_spanish() -> bool:
    """Detecta si el idioma del juego es espanol."""
    try:
        lang = babase.app.lang.language.lower()
    except Exception:
        return False
    return 'spanish' in lang or 'espa\u00f1ol' in lang or lang.startswith('es')


def _fullstore_text(key: str, **values: Any) -> str:
    texts = _FULLSTORE_TEXTS['es' if is_spanish() else 'en']
    text = texts[key]
    return text.format(**values) if values else text


def _get_store_button() -> bui.Widget | None:
    try:
        return bui.get_special_widget('store_button')
    except Exception:
        return None


def _name_for_item(item: str, fallback: str) -> babase.Lstr:
    classic = babase.app.classic
    if classic is None:
        return babase.Lstr(value=fallback)
    try:
        return classic.store.get_store_item_name_translated(item)
    except Exception:
        return babase.Lstr(value=fallback)


def _price_for_item(item: str) -> int | None:
    plus = babase.app.plus
    if plus is None:
        return None
    price = plus.get_v1_account_misc_read_val('price.' + item, None)
    return price if isinstance(price, int) else None


def _name_text_for_item(item: str, fallback: str) -> str:
    try:
        return _name_for_item(item, fallback).evaluate()
    except Exception:
        return fallback


def _show_already_owned() -> None:
    bui.getsound('error').play()
    bui.screenmessage(_fullstore_text('already_owned_message'), color=(1, 1, 0))


def _show_unavailable() -> None:
    bui.getsound('error').play()
    bui.screenmessage(
        _fullstore_text('unavailable_message'),
        color=(1, 0.25, 0.25),
    )


def _purchase_special_character(
    item: str,
    origin_widget: bui.Widget | None = None,
) -> bool:
    plus = bui.app.plus
    classic = bui.app.classic
    if plus is None or classic is None:
        return False

    if item not in SPECIAL_CHARACTER_ITEMS:
        bui.getsound('error').play()
        bui.screenmessage(
            _fullstore_text('unrecognized_character'), color=(1, 0, 0)
        )
        return False

    if plus.accounts.primary is None:
        from bauiv1lib.account.signin import show_sign_in_prompt

        show_sign_in_prompt(origin_widget=origin_widget)
        return False

    if item in classic.purchases:
        _show_already_owned()
        return False

    price = _price_for_item(item)
    if price is None:
        _show_unavailable()
        return False

    if classic.tickets < price:
        bui.getsound('error').play()
        bui.screenmessage(
            bui.Lstr(resource='notEnoughTicketsText'), color=(1, 0, 0)
        )
        return False

    bui.screenmessage(bui.Lstr(resource='purchasingText'), color=(0, 1, 0))
    plus.in_game_purchase(item, price)
    plus.run_v1_account_transactions()
    return True


def _special_character_inventory_button(
    item: str,
    fallback_name: str,
) -> Any:
    import bacommon.docui.v1 as dui1

    classic = babase.app.classic
    appearance = (
        None
        if classic is None
        else classic.spaz_appearances.get(fallback_name)
    )
    price = _price_for_item(item)
    owned = classic is not None and item in classic.purchases

    if owned:
        status_text = _fullstore_text('owned_status')
        status_color = (0.65, 1.0, 0.65, 1.0)
    elif price is None:
        status_text = _fullstore_text('no_price_status')
        status_color = (1.0, 0.65, 0.45, 1.0)
    else:
        status_text = _fullstore_text('buy_with_tickets', price=price)
        status_color = (0.65, 1.0, 0.55, 1.0)

    decorations: list[Any] = []
    if appearance is None:
        decorations.append(
            dui1.Text(
                '?',
                position=(0, 22),
                size=(140, 120),
                scale=2.0,
                color=(0.85, 0.85, 0.95, 1.0),
                flatness=1.0,
                shadow=1.0,
            )
        )
    else:
        decorations.append(
            dui1.Image(
                appearance.icon_texture,
                position=(0, 25),
                size=(140, 140),
                mask_texture='characterIconMask',
                tint_texture=appearance.icon_mask_texture,
                tint_color=appearance.default_color or (1.0, 1.0, 1.0),
                tint2_color=(
                    appearance.default_highlight or (1.0, 1.0, 1.0)
                ),
            )
        )

    decorations.extend(
        [
            dui1.Text(
                _name_text_for_item(item, fallback_name),
                position=(0, -72),
                size=(140, 32),
                scale=0.68,
                color=(0.78, 1.0, 0.70, 1.0),
                flatness=1.0,
                shadow=1.0,
            ),
            dui1.Text(
                status_text,
                position=(0, -95),
                size=(144, 26),
                scale=0.45,
                color=status_color,
                flatness=1.0,
                shadow=0.8,
            ),
        ]
    )

    return dui1.Button(
        texture='white',
        size=(155, 205),
        action=dui1.Local(
            default_sound=True,
            immediate_local_action=FULLSTORE_INVENTORY_ACTION,
            immediate_local_action_args={'item': item},
        ),
        color=(1, 1, 1, 0.0),
        widget_id=f'fullstore.{item}',
        decorations=decorations,
    )


def _special_character_inventory_row(
    characters: tuple[tuple[str, str], ...] = SPECIAL_CHARACTERS,
) -> Any:
    import bacommon.docui.v1 as dui1

    return dui1.ButtonRow(
        title=f"{_fullstore_text('inventory_row_title')} ({len(characters)})",
        title_color=(0.78, 1.0, 0.70, 1.0),
        title_flatness=1.0,
        title_shadow=1.0,
        button_spacing=15,
        padding_left=13,
        padding_bottom=18,
        spacing_bottom=15,
        buttons=[
            _special_character_inventory_button(item, fallback_name)
            for item, fallback_name in characters
        ],
    )


def _response_texts(response: Any) -> set[str]:
    import bacommon.docui.v1 as dui1

    texts: set[str] = set()
    for row in response.page.rows:
        if not isinstance(row, dui1.ButtonRow):
            continue
        if row.title:
            texts.add(row.title.lower())
        if row.subtitle:
            texts.add(row.subtitle.lower())
        for button in row.buttons:
            if button.label:
                texts.add(button.label.lower())
            if button.decorations is None:
                continue
            for decoration in button.decorations:
                if isinstance(decoration, dui1.Text):
                    texts.add(decoration.text.lower())
    return texts


def _text_already_visible(text: str, visible_texts: set[str]) -> bool:
    text = text.lower()
    return any(text == visible or text in visible for visible in visible_texts)


def _missing_special_characters(response: Any) -> tuple[tuple[str, str], ...]:
    visible_texts = _response_texts(response)
    missing: list[tuple[str, str]] = []

    for item, fallback_name in SPECIAL_CHARACTERS:
        visible_name = _name_text_for_item(item, fallback_name)
        if _text_already_visible(visible_name, visible_texts):
            continue
        if _text_already_visible(fallback_name, visible_texts):
            continue
        missing.append((item, fallback_name))

    return tuple(missing)


def _add_special_character_row(request: Any, response: Any) -> Any:
    import bacommon.docui.v1 as dui1

    if not (
        isinstance(request, dui1.Request)
        and isinstance(response, dui1.Response)
        and request.path == '/'
    ):
        return response

    rows = response.page.rows
    for row in rows:
        if (
            isinstance(row, dui1.ButtonRow)
            and row.title is not None
            and any(
                row.title.startswith(title)
                for title in FULLSTORE_INVENTORY_ROW_TITLES
            )
        ):
            return response

    missing_characters = _missing_special_characters(response)
    if not missing_characters:
        return response

    insert_index: int | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, dui1.ButtonRow) or not row.title:
            continue

        title = row.title.lower()
        if (
            '"r":"store.yourcharacterstext"' in title
            or 'character' in title
            or 'personaje' in title
        ):
            insert_index = index + 1

    if insert_index is None:
        rows.append(_special_character_inventory_row(missing_characters))
    else:
        rows.insert(
            insert_index, _special_character_inventory_row(missing_characters)
        )

    return response


def _patched_inventory_fulfill_request(self: Any, request: Any) -> Any:
    original = getattr(type(self), '_fullstore_original_fulfill_request')
    response = original(self, request)
    return _add_special_character_row(request, response)


def _patched_store_fulfill_request(self: Any, request: Any) -> Any:
    original = getattr(type(self), '_fullstore_original_fulfill_request')
    response = original(self, request)
    return _add_special_character_row(request, response)


def _refresh_docui_window(controller: Any, window: Any) -> None:
    try:
        controller.replace(window, window.request, is_refresh=True)
    except Exception:
        bui.uilog.exception('Error refreshing FullStore row.')


def _handle_special_character_local_action(
    controller: Any,
    action: Any,
) -> bool:
    if action.name != FULLSTORE_INVENTORY_ACTION:
        return False

    item = action.args.get('item')
    if not isinstance(item, str):
        bui.getsound('error').play()
        bui.screenmessage(
            _fullstore_text('invalid_purchase_action'), color=(1, 0, 0)
        )
        return True

    if _purchase_special_character(item, origin_widget=action.widget):
        bui.apptimer(
            0.75,
            bui.CallStrict(_refresh_docui_window, controller, action.window),
        )
    return True


def _patched_inventory_local_action(self: Any, action: Any) -> None:
    if _handle_special_character_local_action(self, action):
        return

    original = getattr(type(self), '_fullstore_original_local_action')
    original(self, action)


def _patched_store_local_action(self: Any, action: Any) -> None:
    if _handle_special_character_local_action(self, action):
        return

    original = getattr(type(self), '_fullstore_original_local_action')
    original(self, action)


def _patched_get_store_layout(self: StoreSubsystem) -> dict[str, list[dict[str, Any]]]:
    original = getattr(StoreSubsystem, '_fullstore_original_get_store_layout')
    store_layout = original(self)

    if 'characters' not in store_layout:
        store_layout['characters'] = [{'items': []}]
    if not store_layout['characters']:
        store_layout['characters'].append({'items': []})

    items = store_layout['characters'][0].setdefault('items', [])
    for item, _name in SPECIAL_CHARACTERS:
        if item not in items:
            items.append(item)

    return store_layout


class SpecialCharactersStoreWindow(bui.MainWindow):
    """Small local store for seasonal classic characters."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        uiscale = bui.app.ui_v1.uiscale
        self._width = 720 if uiscale is bui.UIScale.SMALL else 570
        self._height = 430 if uiscale is bui.UIScale.SMALL else 360
        scale = (
            1.6
            if uiscale is bui.UIScale.SMALL
            else 1.15 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=scale,
                toolbar_visibility='menu_full',
                toolbar_cancel_button_style='close',
            ),
            transition=transition,
            origin_widget=origin_widget,
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = bui.get_special_widget('back_button')
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|back',
                position=(42, self._height - 75),
                size=(60, 60),
                scale=0.78,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.CLOSE),
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 48),
            size=(0, 0),
            text=_fullstore_text('inventory_row_title'),
            scale=1.1,
            h_align='center',
            v_align='center',
            color=(0.9, 0.9, 1.0),
            maxwidth=self._width * 0.65,
        )

        self._ticket_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 82),
            size=(0, 0),
            text='',
            scale=0.75,
            h_align='center',
            v_align='center',
            color=(0.65, 0.75, 0.9),
            maxwidth=self._width * 0.8,
        )

        self._buttons: dict[str, bui.Widget] = {}
        self._status_texts: dict[str, bui.Widget] = {}
        self._create_rows()
        self._update_rows()
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCallStrict(self._update_rows), repeat=True
        )

    def _create_rows(self) -> None:
        top = self._height - 142
        row_h = 78
        for index, (item, fallback_name) in enumerate(SPECIAL_CHARACTERS):
            y = top - index * row_h
            self._add_icon(item, fallback_name, 70, y + 9)
            bui.textwidget(
                parent=self._root_widget,
                position=(142, y + 40),
                size=(0, 0),
                text=_name_for_item(item, fallback_name),
                scale=0.83,
                h_align='left',
                v_align='center',
                color=(0.92, 0.92, 0.95),
                maxwidth=220,
            )
            status = bui.textwidget(
                parent=self._root_widget,
                position=(142, y + 13),
                size=(0, 0),
                text='',
                scale=0.58,
                h_align='left',
                v_align='center',
                color=(0.62, 0.68, 0.76),
                maxwidth=250,
            )
            button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|buy_{index}',
                position=(self._width - 178, y + 15),
                size=(135, 46),
                autoselect=True,
                label='...',
                on_activate_call=bui.CallStrict(self._purchase, item),
            )
            self._buttons[item] = button
            self._status_texts[item] = status

        if self._buttons:
            bui.containerwidget(
                edit=self._root_widget,
                selected_child=next(iter(self._buttons.values())),
            )

    def _add_icon(self, item: str, fallback_name: str, x: float, y: float) -> None:
        del item
        classic = bui.app.classic
        appearance = (
            None
            if classic is None
            else classic.spaz_appearances.get(fallback_name)
        )
        if appearance is None:
            bui.textwidget(
                parent=self._root_widget,
                position=(x + 24, y + 24),
                size=(0, 0),
                text='?',
                scale=1.3,
                h_align='center',
                v_align='center',
                color=(0.8, 0.8, 0.85),
            )
            return

        color = appearance.default_color or (1.0, 1.0, 1.0)
        highlight = appearance.default_highlight or (1.0, 1.0, 1.0)
        bui.imagewidget(
            parent=self._root_widget,
            position=(x, y),
            size=(48, 48),
            texture=bui.gettexture(appearance.icon_texture),
            tint_texture=bui.gettexture(appearance.icon_mask_texture),
            tint_color=color,
            tint2_color=highlight,
        )

    def _update_rows(self) -> None:
        plus = bui.app.plus
        classic = bui.app.classic
        if plus is None or classic is None:
            return

        bui.textwidget(
            edit=self._ticket_text,
            text=_fullstore_text('tickets_count', tickets=classic.tickets),
        )

        for item, _fallback_name in SPECIAL_CHARACTERS:
            button = self._buttons[item]
            status = self._status_texts[item]
            price = _price_for_item(item)

            if item in classic.purchases:
                bui.textwidget(
                    edit=status,
                    text=_fullstore_text('already_owned_status'),
                )
                bui.buttonwidget(
                    edit=button,
                    label=_fullstore_text('owned_status'),
                    color=(0.35, 0.45, 0.35),
                    textcolor=(0.72, 0.9, 0.72),
                    on_activate_call=bui.CallStrict(self._already_owned),
                )
            elif price is None:
                bui.textwidget(
                    edit=status,
                    text=_fullstore_text('server_no_price'),
                )
                bui.buttonwidget(
                    edit=button,
                    label=_fullstore_text('unavailable_button'),
                    color=(0.34, 0.34, 0.38),
                    textcolor=(0.58, 0.58, 0.62),
                    on_activate_call=bui.CallStrict(self._unavailable),
                )
            else:
                bui.textwidget(
                    edit=status,
                    text=_fullstore_text('price_with_tickets', price=price),
                )
                bui.buttonwidget(
                    edit=button,
                    label=_fullstore_text('buy_button', price=price),
                    color=(0.25, 0.46, 0.75),
                    textcolor=(0.9, 0.96, 1.0),
                    on_activate_call=bui.CallStrict(self._purchase, item),
                )

    def _purchase(self, item: str) -> None:
        _purchase_special_character(item, origin_widget=self._buttons.get(item))
        self._update_rows()

    def _already_owned(self) -> None:
        _show_already_owned()

    def _unavailable(self) -> None:
        _show_unavailable()


def _open_special_characters_window(
    origin_widget: bui.Widget | None = None,
) -> None:
    ui = bui.app.ui_v1
    if ui.get_main_window() is None:
        ui.set_main_window(
            SpecialCharactersStoreWindow(origin_widget=origin_widget),
            back_state=None,
            is_top_level=True,
            suppress_warning=True,
        )
        return

    ui.auxiliary_window_activate(
        win_type=SpecialCharactersStoreWindow,
        win_create_call=bui.CallStrict(
            SpecialCharactersStoreWindow, origin_widget=origin_widget
        ),
        win_extra_type_id='fullstore.specialcharacters',
    )


def _store_button_press() -> None:
    from bauiv1lib.account.signin import show_sign_in_prompt
    from bauiv1lib.connectivity import wait_for_connectivity

    plus = bui.app.plus
    origin_widget = _get_store_button()
    if plus is None:
        return
    if plus.accounts.primary is None:
        show_sign_in_prompt(origin_widget=origin_widget)
        return

    wait_for_connectivity(
        on_connected=bui.CallStrict(
            _open_special_characters_window, origin_widget=origin_widget
        )
    )


def _patched_root_ui_store_press(self: Any) -> None:
    del self
    _store_button_press()


def _patched_character_picker_store_press(self: Any) -> None:
    from bauiv1lib.account.signin import show_sign_in_prompt

    plus = bui.app.plus
    if plus is None:
        return
    if plus.accounts.primary is None:
        show_sign_in_prompt()
        self._transition_out()
        return

    self._transition_out()
    bui.apptimer(0.12, _open_special_characters_window)


def _install_hooks() -> None:
    from baclassic._appmode import ClassicAppMode
    from bauiv1lib.characterpicker import CharacterPicker
    from bauiv1lib.inventory import InventoryUIController
    from bauiv1lib.store import StoreUIController

    if not hasattr(StoreSubsystem, '_fullstore_original_get_store_layout'):
        StoreSubsystem._fullstore_original_get_store_layout = (
            StoreSubsystem.get_store_layout
        )
    StoreSubsystem.get_store_layout = _patched_get_store_layout

    if hasattr(ClassicAppMode, '_fullstore_original_root_ui_store_press'):
        ClassicAppMode._root_ui_store_press = (
            ClassicAppMode._fullstore_original_root_ui_store_press
        )

    if hasattr(CharacterPicker, '_fullstore_original_on_store_press'):
        CharacterPicker._on_store_press = (
            CharacterPicker._fullstore_original_on_store_press
        )

    try:
        appmode = bui.app.mode
    except Exception:
        appmode = None
    if isinstance(appmode, ClassicAppMode):
        ui = bui.app.ui_v1
        ui.root_ui_calls[ui.RootUIElement.STORE_BUTTON] = (
            appmode._root_ui_store_press
        )

    if not hasattr(StoreUIController, '_fullstore_original_fulfill_request'):
        StoreUIController._fullstore_original_fulfill_request = (
            StoreUIController.fulfill_request
        )
    StoreUIController.fulfill_request = _patched_store_fulfill_request

    if not hasattr(StoreUIController, '_fullstore_original_local_action'):
        StoreUIController._fullstore_original_local_action = (
            StoreUIController.local_action
        )
    StoreUIController.local_action = _patched_store_local_action

    if not hasattr(InventoryUIController, '_fullstore_original_fulfill_request'):
        InventoryUIController._fullstore_original_fulfill_request = (
            InventoryUIController.fulfill_request
        )
    InventoryUIController.fulfill_request = _patched_inventory_fulfill_request

    if not hasattr(InventoryUIController, '_fullstore_original_local_action'):
        InventoryUIController._fullstore_original_local_action = (
            InventoryUIController.local_action
        )
    InventoryUIController.local_action = _patched_inventory_local_action


# ba_meta export babase.Plugin
class ModPlugin(babase.Plugin):
    def __init__(self) -> None:
        _install_hooks()

    def on_app_running(self) -> None:
        _install_hooks()
