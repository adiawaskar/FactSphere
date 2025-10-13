import whois
from datetime import datetime, timezone
import time
import re
from typing import Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

def clean_domain(domain: str) -> str:
    """
    Clean and extract the root domain from a URL
    """
    try:
        # Remove protocol
        domain = re.sub(r'^https?://', '', domain)
        
        # Remove path and query parameters
        domain = domain.split('/')[0]
        
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        
        # Remove port numbers
        domain = domain.split(':')[0]
        
        return domain.lower().strip()
    except Exception as e:
        logger.warning(f"Error cleaning domain {domain}: {e}")
        return domain

def normalize_datetime(dt) -> Optional[datetime]:
    """
    Normalize datetime to timezone-naive UTC
    """
    if not dt:
        return None
    
    try:
        if isinstance(dt, datetime):
            if dt.tzinfo is not None:
                # Convert to UTC and remove timezone info
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                # Already timezone-naive, assume UTC
                return dt
        return None
    except Exception as e:
        logger.warning(f"Error normalizing datetime {dt}: {e}")
        return None

def extract_creation_date(creation_date) -> Optional[datetime]:
    """
    Extract creation date from various WHOIS response formats with timezone handling
    """
    if not creation_date:
        return None
    
    try:
        # Handle list of dates
        if isinstance(creation_date, list):
            # Normalize all dates and get the earliest one
            normalized_dates = []
            for date_item in creation_date:
                normalized = normalize_datetime(date_item)
                if normalized:
                    normalized_dates.append(normalized)
            
            if normalized_dates:
                return min(normalized_dates)
            return None
        
        # Handle string dates
        elif isinstance(creation_date, str):
            # Try common date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d-%b-%Y',
                '%b %d %Y',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%Y-%m-%d %H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S %Z'
            ]
            
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(creation_date, date_format)
                    return normalize_datetime(parsed_date)
                except ValueError:
                    continue
            return None
        
        # Handle datetime object directly
        elif isinstance(creation_date, datetime):
            return normalize_datetime(creation_date)
        
        else:
            logger.warning(f"Unexpected creation date format: {type(creation_date)} - {creation_date}")
            return None
            
    except Exception as e:
        logger.warning(f"Error extracting creation date from {creation_date}: {e}")
        return None

def get_domain_age_days(domain: str, timeout: int = 10) -> Optional[int]:
    """
    Get domain age in days using WHOIS lookup with robust error handling
    
    Args:
        domain: The domain or URL to check
        timeout: WHOIS query timeout in seconds
    
    Returns:
        int: Domain age in days, or None if lookup failed
    """
    try:
        # Clean the domain
        clean_domain_name = clean_domain(domain)
        
        if not clean_domain_name:
            logger.warning(f"Invalid domain after cleaning: {domain}")
            return None
        
        logger.info(f"Performing WHOIS lookup for: {clean_domain_name}")
        
        # Perform WHOIS lookup with timeout
        start_time = time.time()
        domain_info = whois.whois(clean_domain_name)
        
        # Check if lookup timed out
        if time.time() - start_time > timeout:
            logger.warning(f"WHOIS lookup timed out for: {clean_domain_name}")
            return None
        
        # Extract creation date
        creation_date = extract_creation_date(domain_info.creation_date)
        
        if not creation_date:
            # Try alternative date fields
            alternative_fields = ['creation_date', 'created', 'registered', 'registration_date']
            for field in alternative_fields:
                if hasattr(domain_info, field) and getattr(domain_info, field) != domain_info.creation_date:
                    alt_date = extract_creation_date(getattr(domain_info, field))
                    if alt_date:
                        creation_date = alt_date
                        logger.info(f"Found creation date in alternative field: {field}")
                        break
            
            if not creation_date:
                logger.warning(f"No creation date found in WHOIS data for: {clean_domain_name}")
                # Debug: print available fields
                available_fields = [attr for attr in dir(domain_info) if not attr.startswith('_')]
                logger.debug(f"Available WHOIS fields: {available_fields}")
                return None
        
        # Calculate age in days (both in UTC for fair comparison)
        today = datetime.utcnow()
        age_days = (today - creation_date).days
        
        # Validate the age is reasonable (not future date and not too old)
        if age_days < 0:
            logger.warning(f"Domain creation date is in the future: {creation_date}")
            return None
        elif age_days > 365 * 50:  # More than 50 years
            logger.warning(f"Domain age seems unrealistic: {age_days} days")
            return None
        
        logger.info(f"Domain age for {clean_domain_name}: {age_days} days (created: {creation_date.date()})")
        return age_days
        
    except whois.parser.PywhoisError as e:
        logger.warning(f"WHOIS parsing error for {domain}: {e}")
        return None
    except whois.exceptions.FailedParsingWhoisOutput as e:
        logger.warning(f"WHOIS output parsing failed for {domain}: {e}")
        return None
    except whois.exceptions.UnknownTld as e:
        logger.warning(f"Unknown TLD for {domain}: {e}")
        return None
    except whois.exceptions.UnknownDateFormat as e:
        logger.warning(f"Unknown date format in WHOIS for {domain}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in WHOIS lookup for {domain}: {e}")
        return None

# Enhanced version that handles the specific timezone issue
def get_domain_age_days_enhanced(domain: str, timeout: int = 10) -> Optional[int]:
    """
    Enhanced version that specifically handles timezone-aware datetime comparisons
    """
    try:
        # Clean the domain
        clean_domain_name = clean_domain(domain)
        
        if not clean_domain_name:
            return None
        
        logger.info(f"Performing WHOIS lookup for: {clean_domain_name}")
        
        # Perform WHOIS lookup
        start_time = time.time()
        domain_info = whois.whois(clean_domain_name)
        
        if time.time() - start_time > timeout:
            logger.warning(f"WHOIS lookup timed out for: {clean_domain_name}")
            return None
        
        # Handle creation date extraction with better timezone handling
        creation_date = None
        
        # Get the raw creation date field
        raw_creation_date = domain_info.creation_date
        
        if raw_creation_date:
            # If it's a list, find the earliest valid date
            if isinstance(raw_creation_date, list):
                valid_dates = []
                for date_item in raw_creation_date:
                    if isinstance(date_item, datetime):
                        # Convert all to timezone-naive UTC for comparison
                        if date_item.tzinfo is not None:
                            normalized = date_item.astimezone(timezone.utc).replace(tzinfo=None)
                        else:
                            normalized = date_item
                        valid_dates.append(normalized)
                
                if valid_dates:
                    creation_date = min(valid_dates)
                    logger.info(f"Selected earliest date from list: {creation_date}")
            
            # If it's a single datetime
            elif isinstance(raw_creation_date, datetime):
                if raw_creation_date.tzinfo is not None:
                    creation_date = raw_creation_date.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    creation_date = raw_creation_date
            
            # If it's a string, try to parse it
            elif isinstance(raw_creation_date, str):
                creation_date = extract_creation_date(raw_creation_date)
        
        if not creation_date:
            logger.warning(f"No valid creation date found for: {clean_domain_name}")
            return None
        
        # Calculate age using UTC for both dates
        today_utc = datetime.utcnow()
        age_days = (today_utc - creation_date).days
        
        # Validate age
        if age_days < 0:
            logger.warning(f"Domain creation date is in the future: {creation_date}")
            return None
        elif age_days > 365 * 50:
            logger.warning(f"Domain age seems unrealistic: {age_days} days")
            return None
        
        logger.info(f"Domain age for {clean_domain_name}: {age_days} days (created: {creation_date.date()})")
        return age_days
        
    except Exception as e:
        logger.error(f"Error in enhanced domain age lookup for {domain}: {e}")
        return None

# Usage in your credibility scoring (updated):
def calculate_domain_credibility(domain: str) -> tuple[float, list[str], dict]:
    """
    Calculate domain credibility including age assessment
    """
    score = 0.15  # Base score
    reasons = ""
    signals = {}
    
    try:
        # Use the enhanced version that handles timezone issues
        age_days = get_domain_age_days_enhanced(domain)
        signals["domain_age_days"] = age_days
        
        if age_days is not None:
            if age_days > 3650:  # > 10 years
                score += 0.08
                reasons="✅ Domain >10 years old (established)"
                logger.info(f"Added +0.08 for established domain: {age_days} days")
            elif age_days > 1825:  # > 5 years
                score += 0.05
                reasons="✅ Domain 5-10 years old (mature)"
                logger.info(f"Added +0.05 for mature domain: {age_days} days")
            elif age_days > 365:  # > 1 year
                score += 0.02
                reasons="✅ Domain 1-5 years old (developing)"
                logger.info(f"Added +0.02 for developing domain: {age_days} days")
            elif age_days < 180:  # < 6 months
                score -= 0.15
                reasons="⚠️ Domain <6 months old (recent)"
                logger.info(f"Subtracted -0.15 for new domain: {age_days} days")
            elif age_days < 365:  # < 1 year
                score -= 0.08
                reasons="⚠️ Domain 6-12 months old (new)"
                logger.info(f"Subtracted -0.08 for new domain: {age_days} days")
            else:
                reasons="ℹ️ Domain age neutral"
        else:
            score -= 0.05
            reasons="❌ WHOIS lookup failed"
            logger.info("Subtracted -0.05 for failed WHOIS lookup")
            
    except Exception as e:
        logger.error(f"Error in domain credibility calculation: {e}")
        reasons="❌ Domain age check failed"
        signals["domain_age_days"] = None
    
    return score, reasons, signals

# Test function
def test_domain_age():
    """Test the domain age function with various domains"""
    test_domains = [
        "keshavdhanukastd12.com",
        "github.com", 
        "example.com",
        "invalid-domain-that-doesnt-exist-12345.com",
        "https://www.livemint.com/news/world/some-article",
        "http://localhost:3000",
        "subdomain.example.co.uk"
    ]
    
    for domain in test_domains:
        print(f"\nTesting: {domain}")
        age_days = get_domain_age_days_enhanced(domain)
        if age_days:
            years = age_days / 365
            print(f"✅ Age: {age_days} days ({years:.1f} years)")
        else:
            print("❌ Failed to get domain age")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    test_domain_age()