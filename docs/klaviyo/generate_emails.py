import os, html
OUT = '/home/user/shopify/docs/klaviyo/emails'
CDN = 'https://cdn.shopify.com/s/files/1/1092/4212/2609/files/'
LOGO = CDN + 'vitalray-logo-email.png?v=1793618315'
IMG = {
  'hands': CDN + 'vitalray-hero-hands.png?v=1793555410',
  'reading': CDN + 'vitalray-lifestyle-reading.png?v=1793555410',
  'desk': CDN + 'vitalray-lifestyle-desk.png?v=1793555410',
}
SHOP = 'https://vitalray.shop'
PDP = SHOP + '/products/vitalray-wrist'
INK, MUTED, CORAL, CREAM, SAGE, LINE, BLUSH = '#1F2A27', '#5B6662', '#C4502F', '#F5F3EE', '#E4EBE3', '#E3DED5', '#F6E3DB'
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"

def button(label, url):
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:8px auto 4px;">
  <tr><td align="center" bgcolor="{CORAL}" style="border-radius:10px;">
    <a href="{url}" target="_blank" style="display:inline-block;padding:16px 34px;font-family:{SANS};font-size:16px;font-weight:bold;letter-spacing:.5px;color:#ffffff;text-decoration:none;border-radius:10px;">{label} &rarr;</a>
  </td></tr></table>'''

def p(text, size=16, color=MUTED, align='left', mb=16):
    return f'<p style="margin:0 0 {mb}px;font-family:{SANS};font-size:{size}px;line-height:1.6;color:{color};text-align:{align};">{text}</p>'

def h1(text, align='left'):
    return f'<h1 style="margin:0 0 14px;font-family:{SERIF};font-size:32px;line-height:1.2;font-weight:normal;color:{INK};text-align:{align};">{text}</h1>'

def h2(text):
    return f'<h2 style="margin:24px 0 10px;font-family:{SERIF};font-size:22px;line-height:1.3;font-weight:normal;color:{INK};">{text}</h2>'

def eyebrow(text, align='left'):
    return f'<p style="margin:0 0 10px;font-family:{SANS};font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{CORAL};text-align:{align};">{text}</p>'

def checklist(items):
    rows = ''.join(f'''<tr><td valign="top" width="30" style="padding:0 0 12px;"><div style="width:22px;height:22px;border-radius:11px;background:{BLUSH};color:{CORAL};font:bold 13px/22px {SANS};text-align:center;">&#10003;</div></td>
<td style="padding:0 0 12px;font-family:{SANS};font-size:15px;line-height:1.55;color:{MUTED};"><strong style="color:{INK};">{t}</strong> {d}</td></tr>''' for t,d in items)
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 18px;">{rows}</table>'

def steps(items):
    rows = ''.join(f'''<tr><td valign="top" width="44" style="padding:0 0 16px;"><div style="width:32px;height:32px;border-radius:16px;background:{CORAL};color:#fff;font:bold 15px/32px {SANS};text-align:center;">{i}</div></td>
<td style="padding:0 0 16px;font-family:{SANS};font-size:15px;line-height:1.55;color:{MUTED};"><strong style="color:{INK};font-size:16px;">{t}</strong><br>{d}</td></tr>''' for i,(t,d) in enumerate(items,1))
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 14px;">{rows}</table>'

def callout(title, text, bg=SAGE):
    return f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:10px 0 20px;"><tr>
<td style="background:{bg};border-radius:14px;padding:18px 20px;font-family:{SANS};font-size:15px;line-height:1.55;color:{MUTED};"><strong style="display:block;color:{INK};font-size:16px;margin-bottom:4px;">{title}</strong>{text}</td></tr></table>'''

def image(key, alt):
    return f'<img src="{IMG[key]}" width="600" alt="{alt}" style="display:block;width:100%;max-width:600px;height:auto;border:0;">'

def bundle_box():
    return callout('Treat both hands &mdash; save 15%', 'Add 2 VitalRay Wrists to your cart and an extra 15% comes off automatically at checkout. No code needed.', BLUSH)

TRUST = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid {LINE};">
<tr>
<td width="33%" align="center" style="padding:18px 6px;font-family:{SANS};font-size:12px;line-height:1.4;color:{INK};"><strong>Free tracked</strong><br><span style="color:{MUTED};">shipping</span></td>
<td width="34%" align="center" style="padding:18px 6px;font-family:{SANS};font-size:12px;line-height:1.4;color:{INK};border-left:1px solid {LINE};border-right:1px solid {LINE};"><strong>90-day</strong><br><span style="color:{MUTED};">money-back guarantee</span></td>
<td width="33%" align="center" style="padding:18px 6px;font-family:{SANS};font-size:12px;line-height:1.4;color:{INK};"><strong>Real humans</strong><br><span style="color:{MUTED};">reply in 1 business day</span></td>
</tr></table>'''

def layout(preheader, hero_key, hero_alt, body, title):
    hero = image(hero_key, hero_alt) if hero_key else ''
    return f'''<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="x-apple-disable-message-reformatting">
<title>{html.escape(title)}</title>
<style>
  @media only screen and (max-width:620px) {{
    .vr-wrap {{ width:100% !important; }}
    .vr-pad {{ padding-left:22px !important; padding-right:22px !important; }}
    h1 {{ font-size:27px !important; }}
  }}
  a {{ color:{CORAL}; }}
</style>
</head>
<body style="margin:0;padding:0;background:{CREAM};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{CREAM};">{preheader}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{CREAM}">
<tr><td align="center" style="padding:24px 12px;">
  <table role="presentation" class="vr-wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;">
    <tr><td align="center" style="padding:6px 0 18px;font-family:{SANS};font-size:12px;color:{MUTED};">Free tracked shipping to the US, CA, UK &amp; AU &middot; {{% web_view %}}</td></tr>
    <tr><td align="center" style="padding:0 0 20px;"><a href="{SHOP}" target="_blank"><img src="{LOGO}" width="170" alt="VitalRay" style="display:block;width:170px;height:auto;border:0;"></a></td></tr>
    <tr><td bgcolor="#ffffff" style="background:#ffffff;border-radius:18px;overflow:hidden;">
      {hero}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td class="vr-pad" style="padding:34px 40px 26px;">
        {body}
      </td></tr></table>
      {TRUST}
    </td></tr>
    <tr><td align="center" style="padding:26px 20px 8px;font-family:{SANS};font-size:12px;line-height:1.7;color:{MUTED};">
      Questions? Just reply to this email or write to <a href="mailto:support@vitalray.shop" style="color:{CORAL};">support@vitalray.shop</a><br>
      <a href="{SHOP}/pages/faq" style="color:{MUTED};">FAQ</a> &nbsp;&middot;&nbsp; <a href="{SHOP}/pages/track-order" style="color:{MUTED};">Track order</a> &nbsp;&middot;&nbsp; <a href="{SHOP}/policies/refund-policy" style="color:{MUTED};">Returns</a><br><br>
      <span style="font-size:11px;">*VitalRay products are not intended to diagnose, treat, cure or prevent any disease.</span><br>
      <span style="font-size:11px;">{{{{ organization.name }}}} &middot; {{{{ organization.full_address }}}}</span><br>
      <span style="font-size:11px;">{{% unsubscribe 'Unsubscribe' %}} &nbsp;&middot;&nbsp; {{% manage_preferences 'Email preferences' %}}</span>
    </td></tr>
  </table>
</td></tr></table>
</body></html>
'''

HI = 'Hi {{ first_name|default:"there" }},'
CART = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 22px;border:1px solid {LINE};border-radius:14px;">
{{% for item in event.extra.line_items %}}
<tr>
  <td width="88" style="padding:14px 0 14px 14px;"><img src="{{{{ item.product.images.0.src }}}}" width="72" alt="{{{{ item.product.title }}}}" style="display:block;width:72px;height:72px;object-fit:cover;border-radius:10px;border:0;"></td>
  <td style="padding:14px;font-family:{SANS};font-size:15px;line-height:1.45;color:{INK};"><strong>{{{{ item.product.title|truncatechars:48 }}}}</strong><br><span style="color:{MUTED};font-size:13px;">Qty {{{{ item.quantity|floatformat:0 }}}}</span></td>
  <td align="right" style="padding:14px 16px 14px 0;font-family:{SANS};font-size:15px;color:{INK};white-space:nowrap;">{{{{ item.line_price|floatformat:2 }}}}</td>
</tr>
{{% endfor %}}
</table>'''
CHECKOUT = '{{ event.extra.checkout_url }}'

EMAILS = {
# ---------------- Welcome series ----------------
'01-welcome-1-hello.html': dict(
  subject='Welcome to VitalRay ☀️', preheader='Gentle red light care for hard-working hands — here’s what to expect.',
  hero=('reading','Woman relaxing on a sofa with a book'),
  body=eyebrow('Welcome') + h1('Care for the hands that <em style="color:#C4502F;">do everything</em>') + p(HI, color=INK) +
    p('Thanks for joining the VitalRay list. We make one thing, and we try to make it really well: a cordless red and near-infrared light wrap for hands and wrists that you can use at home in 15 minutes a day.') +
    h2('Why people love it') + checklist([
      ('Two wavelengths in one wrap', '— red (660nm) and near-infrared (850nm) light.'),
      ('Cordless &amp; USB-C rechargeable', '— use it at your desk, on the couch or in bed.'),
      ('Simple', '— one button, adjustable intensity and a built-in 15-minute timer.')]) +
    button('Meet VitalRay Wrist', PDP) + p('Over the next few days we’ll send a couple of short emails: how to use it, and how our 90-day guarantee works. No spam, ever.', size=14, align='center', mb=0)),
'02-welcome-2-how-to.html': dict(
  subject='How to use VitalRay in 3 simple steps', preheader='15 minutes a day. No appointments, no setup.',
  hero=('desk','Man stretching his wrists at a desk'),
  body=eyebrow('Easy as it gets') + h1('Three steps, 15 minutes') + p(HI, color=INK) +
    p('The best routine is the one you actually keep. Here’s how most people fit VitalRay into their day:') +
    steps([('Wrap it on','Slide your thumb through the loop and fasten the strap over your wrist.'),
           ('Press start','One button starts a 15-minute session. Begin on the lowest intensity.'),
           ('Relax &amp; repeat','Read, watch TV or work. Once a day — consistency matters more than intensity.')]) +
    callout('Good to know','Talk to your doctor first if you are pregnant, have a pacemaker or other implanted device, are light-sensitive, or have a medical condition.') +
    button('Shop VitalRay Wrist', PDP)),
'03-welcome-3-guarantee.html': dict(
  subject='Try it for 90 days — on us', preheader='Free tracked shipping, a 90-day money-back guarantee and 15% off two.',
  hero=('hands','Relaxed hands on a desk in warm light'),
  body=eyebrow('Risk-free') + h1('Try it for 90 days, <em style="color:#C4502F;">risk-free</em>') + p(HI, color=INK) +
    p('We want you to love your VitalRay. Use it every day — if you’re not happy with it within 90 days of delivery, email us and we’ll refund you.') +
    checklist([('Free tracked shipping','to the US, Canada, the UK and Australia.'),
               ('Ships in 1–3 business days,','usually delivered in 7–15.'),
               ('Real humans','reply to every email within one business day.')]) +
    bundle_box() + button('Get VitalRay Wrist', PDP)),
# ---------------- Abandoned checkout ----------------
'04-checkout-1-reminder.html': dict(
  subject='You left something behind', preheader='Your VitalRay is still in your cart.',
  hero=None,
  body=eyebrow('Your cart') + h1('Still thinking it over?') + p(HI, color=INK) +
    p('You left this in your cart. We’ve saved it for you — pick up right where you left off.') + CART +
    button('Return to checkout', CHECKOUT) + p('Free tracked shipping &middot; 90-day money-back guarantee', size=13, align='center', mb=0)),
'05-checkout-2-questions.html': dict(
  subject='Any questions before you order?', preheader='Quick answers about using VitalRay, shipping and returns.',
  hero=('reading','Woman relaxing on a sofa with a book'),
  body=eyebrow('We’re here to help') + h1('Questions before you order?') + p(HI, color=INK) +
    p('Here are the answers people ask for most often:') +
    h2('How often should I use it?') + p('Most people use it once a day for a 15-minute session. It turns off automatically.') +
    h2('How long does shipping take?') + p('Orders ship in 1–3 business days and usually arrive in 7–15, with free tracking.') +
    h2('What if it’s not for me?') + p('You have 90 days from delivery to request a refund. Just email us.') +
    button('Complete my order', CHECKOUT) + p('Something else? Reply to this email — a real person will answer.', size=14, align='center', mb=0)),
'06-checkout-3-bundle.html': dict(
  subject='Last reminder: your cart + 15% off two', preheader='Treat both hands and save 15% automatically.',
  hero=None,
  body=eyebrow('Last reminder') + h1('Your cart is about to expire') + p(HI, color=INK) +
    p('Your VitalRay is still waiting. If both hands need some care, add a second wrap — an extra 15% comes off automatically at checkout.') + CART +
    bundle_box() + button('Finish checking out', CHECKOUT)),
# ---------------- Browse abandonment ----------------
'07-browse-1.html': dict(
  subject='Still thinking about {{ event.ProductName|default:"VitalRay Wrist" }}?', preheader='Cordless red light care, 15 minutes a day.',
  hero=None,
  body=eyebrow('Picked for you') + h1('Still thinking about it?') + p(HI, color=INK) +
    p('You were looking at this earlier:') +
    f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 22px;border:1px solid {LINE};border-radius:14px;"><tr>
<td width="140" style="padding:14px;"><img src="{{{{ event.ImageURL }}}}" width="120" alt="{{{{ event.ProductName }}}}" style="display:block;width:120px;height:auto;border-radius:10px;border:0;"></td>
<td style="padding:14px 16px 14px 0;font-family:{SANS};font-size:16px;line-height:1.45;color:{INK};"><strong>{{{{ event.ProductName }}}}</strong><br><span style="color:{MUTED};font-size:14px;">Red &amp; near-infrared light &middot; cordless &middot; 15-minute sessions</span></td></tr></table>''' +
    checklist([('Free tracked shipping','to the US, CA, UK &amp; AU'), ('90-day money-back guarantee','if it’s not for you')]) +
    button('Take another look', '{{ event.URL|default:"' + PDP + '" }}')),
# ---------------- Post-purchase ----------------
'08-post-1-thank-you.html': dict(
  subject='Thank you! Here’s what happens next', preheader='Your order is in. Here’s the timeline.',
  hero=('hands','Relaxed hands on a desk in warm light'),
  body=eyebrow('Order confirmed') + h1('Thank you, {{ first_name|default:"friend" }}!') +
    p('We’re so glad you’re here. Your order confirmation is in a separate email — here’s what happens next:') +
    steps([('We pack your order','Orders leave our fulfillment center within 1–3 business days.'),
           ('You get a tracking link','We email it as soon as your order ships. Tracking can take 2–3 days to update.'),
           ('It arrives','Usually within 7–15 business days, with free tracking.')]) +
    callout('Need to change something?','Reply to this email within 12 hours of ordering if you need to update your address.') +
    button('Track my order', SHOP + '/pages/track-order')),
'09-post-2-getting-started.html': dict(
  subject='Getting the most out of your VitalRay', preheader='A few tips for your first two weeks.',
  hero=('desk','Man stretching his wrists at a desk'),
  body=eyebrow('Getting started') + h1('Your first two weeks') + p(HI, color=INK) +
    p('Your VitalRay should be with you soon (or already is). A few tips from our team:') +
    checklist([('Charge it fully first','using the included USB-C cable.'),
               ('Start low','— begin on the lowest intensity and adjust to what feels comfortable.'),
               ('Pair it with a habit','— morning coffee, an evening show, your lunch break.'),
               ('Stay consistent','— one 15-minute session a day.')]) +
    callout('Safety first','Stop a session if it ever feels uncomfortable. Check with your doctor if you have a medical condition, are pregnant, or have an implanted device.') +
    p('Questions? Just reply — we answer every email within one business day.', mb=0)),
'10-post-3-feedback.html': dict(
  subject='How’s it going with your VitalRay?', preheader='We’d love to hear from you.',
  hero=('reading','Woman relaxing on a sofa with a book'),
  body=eyebrow('We’d love your feedback') + h1('How’s it going?') + p(HI, color=INK) +
    p('You’ve had your VitalRay for a few weeks now. We read every reply and use it to make VitalRay better.') +
    p('If something isn’t right, please tell us — remember you’re covered by our 90-day money-back guarantee.') +
    button('Reply to us', 'mailto:support@vitalray.shop?subject=My%20VitalRay%20feedback') +
    p('If you’re enjoying it, an honest review on our product page helps other people decide. Thank you!', size=14, align='center', mb=0)),
}

import json
meta = {}
for name, e in EMAILS.items():
    hero = e['hero']
    out = layout(e['preheader'], hero[0] if hero else None, hero[1] if hero else '', e['body'], e['subject'])
    open(os.path.join(OUT, name), 'w').write(out)
    meta[name] = {'subject': e['subject'], 'preheader': e['preheader']}
json.dump(meta, open(os.path.join(OUT, '_subjects.json'), 'w'), indent=2, ensure_ascii=False)
print(len(EMAILS), 'emails written')
