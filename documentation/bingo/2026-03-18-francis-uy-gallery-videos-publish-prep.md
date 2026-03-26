# Bingo: Francis Uy Advisor, Gallery Videos, Gallery Cleanup

**Date:** 2026-03-18  
**Environment:** Azure Nightingale staging (`azure-nightingale-589250.hostingersite.com`)  
**Operator:** CC (desktop)

## Summary

Pre-publish session: added Francis Uy as advisor, populated Gallery Videos with YouTube embeds, and cleaned up Gallery Images. Site targeting same-day publish to polysaas.online.

## Changes Made

### Francis Uy — Advisor Card (About Us)
- **Headshot uploaded** to WP media (`francis-uy-headshot.jpg`, ID 2570)
- **Full advisor card added** between Feyzi Fatehi and John Shackleton
- **Title:** CEO, Katapult Digital & Sinag Solutions
- **Bio highlights:** Founding Chairman of the Association of Enterprise Architects Philippines; TOGAF-certified & PMP; Master's in Enterprise Architecture Management; led Philippine Covid Vaccine Information Management System and World Bank Group digital government initiatives; 15+ years enterprise systems, 11 years ERP across 4 continents, 9+ years digital marketing/eCommerce/loyalty
- **LinkedIn:** https://www.linkedin.com/in/francisduy/

### Advisor Reorder (About Us)
Reordered advisor cards to reflect relative value:
1. Feyzi Fatehi — Chairman & CEO, Corent Technology
2. John Shackleton — Advisor
3. Francis Uy — CEO, Katapult Digital & Sinag Solutions
4. Scott Chate — VP Partner & Market Development, Corent Technology

### Gallery Videos (gallery-videos page)
- **Replaced "Coming Soon" placeholder** with 3 responsive YouTube embeds
- Videos:
  1. PolySaaS Overview 5 (`_80grF-ht_w`)
  2. PolySniffer feature of PolySaaS (`6-xhFRc54sg`)
  3. About PolySaaS (`XkjQXOTtLFc`)

### Gallery Images Cleanup (gallery-images page)
- **Removed** `3290.jpg` (blank/empty image directly below Mike's headshot)
- **Removed** `7db4423a-e6dd-4f25-be44-213d4ad0affa.jpg` (Topflite aviation/golf diagram — unrelated to PolySaaS)

## Scripts Created
| Script | Purpose |
|--------|---------|
| `update_francis_uy.py` | Upload headshot + add Francis Uy advisor card |
| `reorder_advisors.py` | Reorder advisor cards (Feyzi, John, Francis, Scott) |
| `update_gallery_videos.py` | Replace Coming Soon with 3 YouTube embeds |
| `fix_video_titles.py` | Update video titles to match actual YouTube titles |
| `fix_video_title3.py` | Fix third video title → "About PolySaaS" |
| `remove_topflite.py` | Remove Topflite image from gallery |
| `remove_3290.py` | Remove blank 3290.jpg from gallery |

## Verification
- About Us page: 4 advisor cards in correct order with headshots, bios, and LinkedIn links
- Gallery Videos: 3 embedded YouTube videos with correct titles
- Gallery Images: Topflite and blank images removed

## Next Steps
- Full site review against Sider evaluation framework (consumer, partner, investor impact)
- Publish staging site to polysaas.online via All-in-One WP Migration
