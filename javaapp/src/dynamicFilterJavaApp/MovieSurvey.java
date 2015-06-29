package dynamicFilterJavaApp;

import com.amazonaws.mturk.service.axis.RequesterService;
import com.amazonaws.mturk.service.exception.ServiceException;
import com.amazonaws.mturk.util.PropertiesClientConfig;
import com.amazonaws.mturk.requester.HIT;

/**
 * The MovieSurvey sample application creates a simple HIT using the
 * Amazon Mechanical Turk SDK for Java. The file mturk.properties must be found in the current file path.
 */
public class MovieSurvey{

   private RequesterService service;

   // Define the properties of the HIT to be created.
   private String title = "Movie Survey";
   private String description = 
    "This is a survey to find out how many movies you have watched recently.";
   private int numAssignments = 100;
   private double reward = 0.05;

   /**
    * Constructor
    */
   public MovieSurvey()
   {
      service = new RequesterService(new PropertiesClientConfig());
   }

   /**
    * Create a simple survey.
    * 
    */
   public void createMovieSurvey()
   {
     try 
     {
       // The createHIT method is called using a convenience static method 
       // RequesterService.getBasicFreeTextQuestion() that generates the question format
       // for the HIT.
       HIT hit = service.createHIT
       (
          title,
          description,
          reward,
          RequesterService.getBasicFreeTextQuestion(
               "How many movies have you seen this month?"),
          numAssignments);
              
       // Print out the HITId and the URL to view the HIT.
       System.out.println("Created HIT: " + hit.getHITId());
       System.out.println("HIT location: ");
       System.out.println(service.getWebsiteURL() + "/mturk/preview?groupId=" + hit.getHITTypeId());
      
    }
    catch (ServiceException e) 
    {
       System.err.println(e.getLocalizedMessage());
    }
  }

   /**
    * Main method
    * 
    * @param args
    */
   public static void main(String[] args)
   {
     // Create an instance of this class.  
     MovieSurvey app = new MovieSurvey();
     
     // Create the new HIT.
     app.createMovieSurvey();
   }
}
