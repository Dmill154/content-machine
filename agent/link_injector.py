"""
Affiliate Link Injector
=======================
Automatically converts product mentions into real Amazon affiliate links.
Handles placeholder links like [Check Price](#) and converts them to real Amazon search URLs.
"""

import re
from typing import Dict, List


class LinkInjector:
    """Injects real Amazon affiliate links into article content."""

    def __init__(self, config: dict):
        self.config = config
        self.affiliate_tag = config.get('affiliate', {}).get('amazon_associate_tag', 'deskdeals-20')

        # Common product patterns to convert to search links
        self.product_patterns = [
            r'\*\*([^*]+(?:Monitor|Chair|Desk|Keyboard|Mouse|Lamp|Stand|Mat|Webcam|Headset|Speaker)[^*]*)\*\*',
            r'###\s*\d*\.?\s*\*?\*?([^#\n]+(?:Monitor|Chair|Desk|Keyboard|Mouse|Lamp|Stand|Mat|Webcam|Headset|Speaker)[^#\n]*)\*?\*?',
            r'####\s*([^#\n]+)',  # H4 headers often contain product names
        ]

        # CTA patterns to convert (plain text)
        self.cta_patterns = [
            (r'[Cc]heck (?:the )?(?:current )?price on Amazon!?\*?\*?', self._make_search_link),
            (r'[Cc]heck (?:it )?out on Amazon!?\*?\*?', self._make_search_link),
            (r'[Ss]ee (?:the )?(?:current )?price on Amazon!?\*?\*?', self._make_search_link),
            (r'[Vv]iew on Amazon!?\*?\*?', self._make_search_link),
            (r'[Bb]uy on Amazon!?\*?\*?', self._make_search_link),
        ]

        # Placeholder link patterns - these are the main culprits!
        self.placeholder_patterns = [
            r'\[Check Price\]\(#\)',
            r'\[Check price\]\(#\)',
            r'\[Buy Now\]\(#\)',
            r'\[View on Amazon\]\(#\)',
            r'\[See Price\]\(#\)',
            r'\[Check Current Price\]\(#\)',
            r'\[Shop Now\]\(#\)',
        ]

    def _make_amazon_search_url(self, product_name: str) -> str:
        """Create Amazon search URL with affiliate tag."""
        # Clean product name for search
        search_term = re.sub(r'[^\w\s-]', '', product_name)
        search_term = search_term.strip().replace(' ', '+')

        base_url = "https://www.amazon.com/s"
        return f"{base_url}?k={search_term}&tag={self.affiliate_tag}"

    def _make_search_link(self, product_context: str) -> str:
        """Create a markdown link for Amazon search."""
        url = self._make_amazon_search_url(product_context)
        return f"[Check price on Amazon]({url})"

    def inject_links(self, content: str, keyword: str) -> str:
        """
        Process article content and inject affiliate links.
        Converts placeholder links like [Check Price](#) to real Amazon links.
        """
        if not self.affiliate_tag:
            self.affiliate_tag = 'deskdeals-20'  # Fallback

        lines = content.split('\n')
        processed_lines = []
        current_product = keyword  # Default context

        for line in lines:
            # Track current product context from headers (H3 and H4)
            header_match = re.search(r'#{3,4}\s*\d*\.?\s*\*?\*?([^#\n*]+)', line)
            if header_match:
                potential_product = header_match.group(1).strip()
                if len(potential_product) > 3:
                    current_product = potential_product

            modified_line = line

            # First: Replace placeholder links [Check Price](#) with real Amazon links
            for pattern in self.placeholder_patterns:
                if re.search(pattern, modified_line, re.IGNORECASE):
                    amazon_url = self._make_amazon_search_url(current_product)
                    replacement = f"[Check Price on Amazon]({amazon_url})"
                    modified_line = re.sub(pattern, replacement, modified_line, flags=re.IGNORECASE)

            # Second: Replace plain text CTA patterns with actual links
            for pattern, link_maker in self.cta_patterns:
                if re.search(pattern, modified_line):
                    link = link_maker(current_product)
                    modified_line = re.sub(pattern, link, modified_line)

            processed_lines.append(modified_line)

        return '\n'.join(processed_lines)

    def add_product_links(self, content: str) -> str:
        """Add Amazon links to specific product mentions."""
        if not self.affiliate_tag:
            return content

        # Find product names in bold and add links if not already linked
        def replace_product(match):
            product_name = match.group(1)
            # Skip if already in a link
            if '](' in product_name or product_name.startswith('['):
                return match.group(0)

            url = self._make_amazon_search_url(product_name)
            return f"**[{product_name}]({url})**"

        # Only link first occurrence of each product
        seen_products = set()
        lines = content.split('\n')
        result_lines = []

        for line in lines:
            # Don't modify headers
            if line.startswith('#'):
                result_lines.append(line)
                continue

            for pattern in self.product_patterns:
                matches = list(re.finditer(pattern, line))
                for match in matches:
                    product = match.group(1).strip()
                    if product not in seen_products and len(product) > 10:
                        seen_products.add(product)
                        url = self._make_amazon_search_url(product)
                        old_text = match.group(0)
                        new_text = f"**[{product}]({url})**"
                        line = line.replace(old_text, new_text, 1)

            result_lines.append(line)

        return '\n'.join(result_lines)

    def process_article(self, content: str, keyword: str) -> str:
        """Full processing pipeline for an article."""
        # First convert ALL placeholder # links to real Amazon links
        content = self._convert_all_placeholder_links(content, keyword)

        # Then inject CTA links (plain text patterns)
        content = self.inject_links(content, keyword)

        # Then add product links to bold product mentions
        content = self.add_product_links(content)

        return content

    def _convert_all_placeholder_links(self, content: str, keyword: str) -> str:
        """
        Convert ALL placeholder links like [anything](#) to Amazon search links.
        This catches any link with href="#" that the AI generates.
        """
        lines = content.split('\n')
        processed_lines = []
        current_product = keyword

        for line in lines:
            # Track product context from headers
            header_match = re.search(r'#{3,4}\s*(.+)', line)
            if header_match:
                header_text = header_match.group(1).strip()
                # Clean markdown formatting
                header_text = re.sub(r'\*+', '', header_text).strip()
                if len(header_text) > 3:
                    current_product = header_text

            # Replace ANY markdown link pointing to # with Amazon link
            # Pattern: [Link Text](#) or [Link Text]( # )
            def replace_placeholder(match):
                link_text = match.group(1)
                amazon_url = self._make_amazon_search_url(current_product)
                return f"[{link_text} on Amazon]({amazon_url})"

            modified_line = re.sub(
                r'\[([^\]]+)\]\(\s*#\s*\)',
                replace_placeholder,
                line
            )

            processed_lines.append(modified_line)

        return '\n'.join(processed_lines)
