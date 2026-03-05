import re
from pathlib import Path


def main() -> None:
    paper_path = Path("../data/input/paper_final.md")
    text = paper_path.read_text(encoding="utf-8")

    marker = "## References"
    if marker not in text:
        raise SystemExit("References section not found")

    pre, post = text.split(marker, 1)

    # Old reference number -> new reference number
    # This mapping is a controlled renumbering while keeping in-text meaning stable.
    mapping = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 10,
        7: 8,
        8: 9,
        9: 7,
        10: 6,
        11: 13,
        12: 15,
        13: 16,
        14: 14,
        15: 12,
        16: 11,
        17: 10,
        18: 23,
        19: 24,
        20: 4,
        21: 5,
        22: 6,
        23: 13,
        24: 15,
        25: 16,
        26: 17,
        27: 3,
        28: 7,
        29: 1,
        30: 8,
        31: 9,
        32: 22,
    }

    refs = [
        "[1] Borrelli MR, Griffin M, Ngaage LM, Longaker MT, Lorenz HP. Striae Distensae: Scars without Wounds. Plast Reconstr Surg. 2021;148(1):77-87. doi:10.1097/PRS.0000000000008065",
        "[2] Atwal GSS, Manku LK, Griffiths CEM, Polson DW. Striae gravidarum in primiparae. Br J Dermatol. 2006;155(5):965-969. doi:10.1111/j.1365-2133.2006.07427.x",
        "[3] Koca枚z S, G枚rdeles Be艧er N, Kizilirmak A. Striae gravidarum in primigravid women: prevalence, risk factors, prevention interventions and body image. J Matern Fetal Neonatal Med. 2019. doi:10.1080/14767058.2019.1591363",
        "[4] Gupta SN, Madke B, Ganjre S, Jawade S, Kondalkar A. Cutaneous Changes During Pregnancy: A Comprehensive Review. Cureus. 2024. doi:10.7759/cureus.69986",
        "[5] Yu Y, Wu H, Yin H, Lu Q. Striae gravidarum and different modalities of therapy: a review and update. J Dermatolog Treat. 2022;33(3):1243-1251. doi:10.1080/09546634.2020.1825614",
        "[6] Farahnik B, Park K, Kroumpouzos G, Murase J. Striae gravidarum: Risk factors, prevention, and management. Int J Womens Dermatol. 2017;3(2):77-85. doi:10.1016/j.ijwd.2016.11.001",
        "[7] Huang Q, Xu LL, Wu T, Mu YZ. New Progress in Therapeutic Modalities of Striae Distensae. Clin Cosmet Investig Dermatol. 2022;15:2101-2115. doi:10.2147/CCID.S379904",
        "[8] Sachs D, Jakob R, Thumm B, Bajka M, Ehret AE, Mazza E. Sustained physiological stretch induces abdominal skin growth in pregnancy. Ann Biomed Eng. 2024;52(6):1576-1590. doi:10.1007/s10439-024-03472-6",
        "[9] Boyer G, Lachmann N, Bellem猫re G, De Belilovsky C, Baudouin C. Effects of pregnancy on skin properties: a biomechanical approach. Skin Res Technol. 2018. doi:10.1111/srt.12465",
        "[10] Mostafavi Yazdi SJ, Baqersad J. Mechanical modeling and characterization of human skin: A review. J Biomech. 2021;130:110864. doi:10.1016/j.jbiomech.2021.110864",
        "[11] Joodaki H, Panzer MB. Skin mechanical properties and modeling: A review. Proc Inst Mech Eng H. 2018;232(4):323-343. doi:10.1177/0954411918759801",
        "[12] Flynn C, Taberner A, Nielsen P. Modeling the mechanical response of in vivo human skin under a rich set of deformations. Ann Biomed Eng. 2011;39(7):1935-1946. doi:10.1007/s10439-011-0292-7",
        "[13] Quintero Rodriguez C, Troynikov O. The Effect of Maternity Support Garments on Alleviation of Pains and Discomforts during Pregnancy: A Systematic Review. Adv Public Health. 2019;2019:2163790. doi:10.1155/2019/2163790",
        "[14] Kalus SM, Kornman LH, Quinlivan JA. Managing back pain in pregnancy using a support garment: a randomised trial. BJOG. 2008;115(1):68-75. doi:10.1111/j.1471-0528.2007.01538.x",
        "[15] Bey ME, Arampatzis A, Legerlotz K. The effect of a maternity support belt on static stability and posture in pregnant and non-pregnant women. J Biomech. 2018;75:123-129. doi:10.1016/j.jbiomech.2018.05.005",
        "[16] Morino S, Ishihara M, Umezaki F, et al. The effects of pelvic belt use on pelvic alignment during and after pregnancy: a prospective longitudinal cohort study. BMC Pregnancy Childbirth. 2019;19:305. doi:10.1186/s12884-019-2457-6",
        "[17] National Institute for Health and Care Excellence (NICE). Pelvic girdle pain in pregnancy: management. In: NCBI Bookshelf. 2021. Available from: https://www.ncbi.nlm.nih.gov/books/NBK573945/",
        "[18] Van Benten E, Pool J, Mens JMA, Pool-Goudzwaard A. Prevention of low back and pelvic girdle pain during pregnancy: a systematic review. Eur J Obstet Gynecol Reprod Biol. 2022. PMID:36288631",
        "[19] Pregnancy and pelvic girdle pain: Analysis of pelvic belt on pain and functional capacity. J Clin Nurs. 2018;27(1-2):e129-e137. doi:10.1111/jocn.13888",
        "[20] Risk factors of striae gravidarum and chloasma melasma and their effects on quality of life. J Cosmet Dermatol. 2023;22(2):603-612. doi:10.1111/jocd.14783",
        "[21] Matyashov T, Pardo E, Rotem R, et al. The association between striae gravidarum and perineal lacerations during labor. PLoS One. 2022;17(3):e0265149. doi:10.1371/journal.pone.0265149",
        "[22] Putra IB, Jusuf NK, Dewi NK. Skin Changes and Safety Profile of Topical Products During Pregnancy. J Clin Aesthet Dermatol. 2022;15(2):49-57. PMID:35309882",
        "[23] Harris CR, Millman KJ, van der Walt SJ, et al. Array programming with NumPy. Nature. 2020;585(7825):357-362. doi:10.1038/s41586-020-2649-2",
        "[24] Virtanen P, Gommers R, Oliphant TE, et al; SciPy 1.0 Contributors. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nat Methods. 2020;17(3):261-272. doi:10.1038/s41592-019-0686-2",
        "[25] Tunzi M, Gray GR. Common skin conditions during pregnancy. Am Fam Physician. 2007;75(2):211-218.",
    ]

    cit_re = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

    def repl(m: re.Match) -> str:
        orig = m.group(0)
        parts = [int(x) for x in re.split(r"\s*,\s*", m.group(1))]
        new_parts = []
        changed = False
        for n in parts:
            if n in mapping:
                new_parts.append(mapping[n])
                changed = True
            else:
                new_parts.append(n)
        new = "[" + ",".join(str(n) for n in new_parts) + "]"
        if changed and new != orig:
            return f"<span style=\"color:blue\">{new}</span>"
        return orig

    pre2 = cit_re.sub(repl, pre)

    # Replace the entire References block with the new list.
    # We cut from '## References' to the next section delimiter '---' (Appendix separator).
    after_marker = post
    cut_idx = after_marker.find("---")
    if cut_idx == -1:
        raise SystemExit("Could not locate end of References section")

    appendix_and_after = after_marker[cut_idx:]

    new_refs_block = "\n\n".join(refs)
    new_text = pre2 + marker + "\n\n" + f"<span style=\"color:blue\">{new_refs_block}</span>\n\n" + appendix_and_after

    paper_path.write_text(new_text, encoding="utf-8")
    print(f"[OK] Renumbered citations and replaced References section. New ref count: {len(refs)}")


if __name__ == "__main__":
    main()

